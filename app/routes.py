import os
import json
import logging
import tempfile
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import db
from .models import JobBrief, CompanyContext, InterviewQuestion, Candidate, Appreciation, User
from .modules.llms import generate_job_description, patch_job_description_required_years
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.utils.therecruit_pdf_template import create_therecruit_pdf


logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

@bp.route('/job-briefs', methods=['POST'])
@jwt_required() # Réactiver le décorateur JWT
@cross_origin(supports_credentials=True, origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], allow_headers=["Content-Type", "Authorization"])
def create_brief():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        # Exiger un context_id
        if not data or 'title' not in data or 'context_id' not in data:
            return jsonify({"error": "Données invalides ou context_id manquant"}), 400
        full_data = generate_job_description({
            "title": data["title"],
            "experience": data.get("experience", "3-5 ans"),
            "description": data.get("description", "")
        })
        full_data = patch_job_description_required_years(full_data, data.get("experience", "3-5 ans"))
        if not full_data or not isinstance(full_data, dict) or not all(k in full_data for k in ["title", "description", "skills", "responsibilities", "qualifications", "required_experience_years", "required_degree"]):
            logger.error(f"Fiche de poste LLM invalide ou vide : {full_data}")
            return jsonify({"error": "La génération de la fiche de poste a échoué. Veuillez réessayer ou modifier les paramètres."}), 502
        brief = JobBrief(
            title=data["title"],
            skills=data.get("skills", []),
            experience=data.get("experience", "3-5 ans"),
            description=data.get("description", ""),
            full_data=json.dumps(full_data),
            user_id=current_user_id,
            context_id=data["context_id"],
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(brief)
        db.session.commit()
        return jsonify({"message": "Fiche créée avec succès", "brief": brief.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de la fiche: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/job-briefs', methods=['GET'])
@jwt_required()
def list_briefs():
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"Récupération des briefs pour l'utilisateur {current_user_id}")
        briefs = JobBrief.query.filter_by(user_id=current_user_id).all()
        logger.info(f"Briefs trouvés : {[brief.title for brief in briefs]}")
        briefs_data = [brief.to_dict() for brief in briefs]
        return jsonify(briefs_data), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des fiches: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

@bp.route('/job-briefs/<int:brief_id>', methods=['GET'])
@jwt_required()
def get_brief_by_id(brief_id):
    try:
        current_user_id = get_jwt_identity()
        brief = JobBrief.query.filter_by(id=brief_id, user_id=current_user_id).first()
        if not brief:
            return jsonify({"error": "Fiche de poste non trouvée", "brief_id": brief_id}), 404
        return jsonify({"status": "success", "data": brief.to_dict()}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la fiche {brief_id}: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

@bp.route('/job-briefs/<int:brief_id>', methods=['PUT'])
@jwt_required()
def update_brief(brief_id):
    try:
        current_user_id = get_jwt_identity()
        brief = JobBrief.query.filter_by(id=brief_id, user_id=current_user_id).first()
        if not brief:
            return jsonify({"error": "Fiche de poste non trouvée"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400

        if 'title' in data or 'experience' in data:
            if not all(key in data for key in ['skills', 'description']):
                logger.info(f"Régénération demandée pour brief {brief_id} avec données minimales")
                full_description = generate_job_description({
                    'title': data.get('title', brief.title),
                    'experience': data.get('experience', brief.experience),
                    'description': data.get('description', brief.description)
                })
                if full_description:
                    # Patch robustesse expérience (stagiaire, 0-1 ans, etc.)
                    full_description = patch_job_description_required_years(full_description, data.get('experience', brief.experience))
                    data['full_data'] = full_description
                    data['skills'] = full_description.get('skills', json.loads(brief.skills) if isinstance(brief.skills, str) else brief.skills)
                    data['description'] = full_description.get('description', data.get('description', brief.description))

        if 'title' in data:
            brief.title = data['title']
        if 'skills' in data:
            brief.skills = json.dumps(data['skills']) if isinstance(data['skills'], list) else data['skills']
        if 'experience' in data:
            brief.experience = data['experience']
        if 'description' in data:
            brief.description = data['description']
        brief.full_data = json.dumps(data.get('full_data', json.loads(brief.full_data) if brief.full_data else {}))
        brief.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Fiche de poste mise à jour",
            "data": brief.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour: {str(e)}")
        return jsonify({"error": "Erreur lors de la mise à jour", "details": str(e)}), 500

@bp.route('/job-briefs/<int:brief_id>', methods=['DELETE'])
@jwt_required()
def delete_brief(brief_id):
    try:
        current_user_id = get_jwt_identity()
        brief = JobBrief.query.filter_by(id=brief_id, user_id=current_user_id).first()
        if not brief:
            return jsonify({"error": "Fiche de poste non trouvée"}), 404

        # Suppression en cascade des candidats liés à ce brief
        from app.models import Candidate
        Candidate.query.filter_by(brief_id=brief_id).delete()

        db.session.delete(brief)
        db.session.commit()

        return jsonify({"status": "success", "message": "Fiche de poste supprimée"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression: {str(e)}")
        return jsonify({"error": "Erreur lors de la suppression", "details": str(e)}), 500

@bp.route('/job-briefs/<int:brief_id>/export-pdf', methods=['GET'])
@jwt_required()
def export_pdf(brief_id):
    try:
        current_user_id = get_jwt_identity()
        brief = JobBrief.query.filter_by(id=brief_id, user_id=current_user_id).first()
        if not brief:
            return jsonify({"error": "Fiche de poste non trouvée"}), 404
        # Construction du contenu pour le template TheRecruit
        # Initialisation des données
        content = []
        # Contexte d'entreprise en haut
        if brief and brief.context_id:
            context = CompanyContext.query.filter_by(id=brief.context_id).first()
            if context:
                try:
                    valeurs = json.loads(context.valeurs) if context.valeurs else []
                except Exception:
                    valeurs = [v.strip() for v in context.valeurs.split(',')] if context.valeurs else []
                content.append({'type': 'label_block', 'label': 'Entreprise', 'value': context.nom_entreprise})
                content.append({'type': 'label_block', 'label': 'Domaine', 'value': context.domaine})
                content.append({'type': 'label_block', 'label': 'Valeurs', 'value': ", ".join(valeurs)})
                content.append({'type': 'label_block', 'label': 'Culture', 'value': context.description_culture})
        # Description
        content.append({'type': 'label_block', 'label': 'Description', 'value': brief.description})
        # Expérience tout en bas
        content.append({'type': 'label_block', 'label': 'Expérience', 'value': brief.experience})
        # Compétences
        skills = brief.skills
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except Exception:
                skills = [skills]
        if skills:
            content.append({'type': 'label_block', 'label': 'Compétences requises', 'value': '\n'.join(f'- {skill}' for skill in skills)})
        if brief.full_data:
            full_data = json.loads(brief.full_data)
            responsibilities = full_data.get('responsibilities', [])
            if responsibilities:
                content.append({'type': 'label_block', 'label': 'Responsabilités', 'value': '\n'.join(f'- {res}' for res in responsibilities)})
            qualifications = full_data.get('qualifications', [])
            if qualifications:
                content.append({'type': 'label_block', 'label': 'Qualifications', 'value': '\n'.join(f'- {q}' for q in qualifications)})

        # Générer le PDF avec le template global
        filename = f"fiche-{brief_id}-{brief.title.replace(' ', '-').lower()}.pdf"
        buffer = BytesIO()
        from app.utils.therecruit_pdf_template import create_therecruit_pdf
        create_therecruit_pdf(buffer, content, title=f"Fiche de poste : {brief.title}")
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except Exception as e:
        logger.error(f"Erreur lors de l'export PDF: {str(e)}")
        return jsonify({"error": "Erreur lors de la génération du PDF", "details": str(e)}), 500

@bp.route('/candidates', methods=['GET'])
@jwt_required()
def get_candidates():
    try:
        current_user_id = get_jwt_identity()
        candidates = Candidate.query.filter_by(user_id=current_user_id).all()
        candidates_data = []
        for c in candidates:
            # Correction parsing interview_questions
            questions = c.interview_questions
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except Exception:
                    questions = []
            elif questions is None:
                questions = []
            candidates_data.append({
                "id": c.id,
                "name": c.name,
                "cv_analysis": json.loads(c.cv_analysis) if c.cv_analysis else None,
                "predictive_score": c.predictive_score,
                "status": c.status,
                "brief_id": c.brief_id,
                "score_details": c.score_details,  # <-- Ajout scores détaillés
                "interview_questions": questions,  # <-- Toujours une liste
                "appreciations": [
                    {
                        "id": a.id,
                        "candidate_id": a.candidate_id,
                        "question": a.question,
                        "category": a.category,
                        "appreciation": a.appreciation,
                        "score": a.score
                    }
                    for a in c.appreciations
                ] if c.appreciations else [],
                "risks": c.risks,  # <-- Ajout risques
                "recommendations": c.recommendations  # <-- Ajout recommandations
            })
        return jsonify(candidates_data), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la fiche {brief_id}: {str(e)}")
        return jsonify({
            "error": "Erreur serveur",
            "details": str(e)
        }), 500

@bp.route('/api/job-briefs', methods=['GET'])
def list_briefs():
    """Lister toutes les fiches de poste"""
    try:
        briefs = JobBrief.query.all()
        briefs_data = [brief.to_dict() for brief in briefs]
        return jsonify(briefs_data), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des fiches: {str(e)}")
        return jsonify({
            "error": "Erreur serveur",
            "details": str(e)
        }), 500

@bp.route('/api/cv', methods=['POST'])
def upload_cv():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    file = request.files['file']
    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)
    cv_text = extract_text_from_pdf(file_path)
    if cv_text.startswith("Erreur"):
        return jsonify({"error": cv_text}), 400
    cv_data = analyze_cv(cv_text)
    if "error" in cv_data:
        return jsonify(cv_data), 500
    brief = JobBrief.query.first()
    if not brief:
        return jsonify({"error": "Aucun brief trouvé"}), 404
    job_desc = json.loads(brief.full_data)
    score_result = calculate_cv_score(cv_data, job_desc)
    visualize_scores(score_result)
    report = generate_final_report(cv_text, cv_data, score_result, job_desc)
    if "error" in report:
        return jsonify(report), 500
    candidate = Candidate(
        name=file.filename.split('.')[0],
        cv_analysis=json.dumps(cv_data),
        predictive_score=0.0,
        status="En évaluation"
    )
    db.session.add(candidate)
    db.session.commit()
    return jsonify({"message": "CV analysé avec succès", "cv_analysis": cv_data, "score": score_result, "report": report}), 201

@bp.route('/api/cv/scores', methods=['GET'])
def get_cv_scores():
    return send_file("cv_scores.png", mimetype='image/png')

@bp.route('/api/context', methods=['POST'])
def create_context():
    data = request.get_json()
    # Conversion de la liste en JSON string
    values_json = json.dumps(data['values'])
    context = CompanyContext(values=values_json, culture=data['culture'])
    db.session.add(context)
    db.session.commit()
    brief = JobBrief.query.first()
    if not brief:
        return jsonify({"error": "Aucun brief trouvé"}), 404
    job_desc = json.loads(brief.full_data)
    candidate = Candidate.query.first()
    if not candidate:
        return jsonify({"error": "Aucun candidat trouvé"}), 404
    cv_data = json.loads(candidate.cv_analysis)
    score_result = calculate_cv_score(cv_data, job_desc)
    questions = generate_interview_questions(job_desc, cv_data, score_result)
    if "error" in questions:
        return jsonify(questions), 500
    for q in questions['questions']:
        question = InterviewQuestion(question=q['question'], category=q['category'], purpose=q['purpose'])
        db.session.add(question)
    db.session.commit()
    return jsonify({"message": "Contexte créé et questions générées", "questions": questions['questions']}), 201

@bp.route('/api/context/questions', methods=['GET'])
def get_questions():
    questions = InterviewQuestion.query.all()
    return jsonify([{"id": q.id, "question": q.question, "category": q.category, "purpose": q.purpose} for q in questions])

@bp.route('/api/evaluation/<int:candidate_id>', methods=['POST'])
def evaluate_candidate(candidate_id):
    data = request.get_json()
    appreciations = data['appreciations']
    for app in appreciations:
        appreciation = Appreciation(
            candidate_id=candidate_id,
            question=app['question'],
            category=app['category'],
            appreciation=app['appreciation'],
            score=app['score']
        )
        db.session.add(appreciation)
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidat non trouvé"}), 404
    cv_data = json.loads(candidate.cv_analysis)
    brief = JobBrief.query.first()
    if not brief:
        return jsonify({"error": "Aucun brief trouvé"}), 404
    job_desc = json.loads(brief.full_data)
    score_result = calculate_cv_score(cv_data, job_desc)
    questions = {"questions": [{"question": q.question, "category": q.category, "purpose": q.purpose} for q in InterviewQuestion.query.all()]}
    analysis = generate_predictive_analysis(job_desc, cv_data, score_result, questions)
    if "error" in analysis:
        return jsonify(analysis), 500
    candidate.predictive_score = analysis['predictive_score']
    candidate.status = "Évalué"
    db.session.commit()
    return jsonify({"message": "Évaluation soumise", "analysis": analysis}), 201

@bp.route('/api/evaluation/radar', methods=['GET'])
def get_radar():
    return send_file("predictive_radar.png", mimetype='image/png')

@bp.route('/api/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "cv_analysis": json.loads(c.cv_analysis) if c.cv_analysis else None,
        "predictive_score": c.predictive_score,
        "status": c.status,
        "appreciations": [{"question": a.question, "category": a.category, "appreciation": a.appreciation, "score": a.score} for a in c.appreciations]
    } for c in candidates])

# Routes d'authentification déplacées vers auth.py
