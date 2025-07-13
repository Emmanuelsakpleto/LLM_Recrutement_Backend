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
from .constants import CANDIDATE_STATUS, PROCESS_STAGES, SCORING_THRESHOLDS, SCORING_WEIGHTS
from .process_manager import ProcessManager
from .modules.llms import (
    generate_job_description,
    extract_text_from_pdf,
    analyze_cv,
    calculate_cv_score,
    visualize_scores,
    generate_final_report,
    generate_interview_questions,
    generate_predictive_analysis
)
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.utils.therecruit_pdf_template import create_therecruit_pdf



logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

# --- ROUTES CONTEXTES ENTREPRISE ---
@bp.route('/api/context', methods=['GET'])
@jwt_required()
def get_contexts():
    current_user_id = get_jwt_identity()
    contexts = CompanyContext.query.filter_by(user_id=current_user_id).all()
    return jsonify([
        {
            'id': c.id,
            'nom_entreprise': getattr(c, 'nom_entreprise', ''),
            'domaine': getattr(c, 'domaine', ''),
            'values': json.loads(c.valeurs) if c.valeurs else [],
            'culture': getattr(c, 'description_culture', '')
        } for c in contexts
    ])
@bp.route('/api/context', methods=['POST'])
@jwt_required()
def create_context():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    values_json = json.dumps(data['values'])
    context = CompanyContext(
        user_id=current_user_id, 
        nom_entreprise=data.get('nom_entreprise', ''),
        domaine=data.get('domaine', ''),
        valeurs=values_json, 
        description_culture=data.get('culture', '')
    )
    db.session.add(context)
    db.session.commit()
    return jsonify({"message": "Contexte créé", "context_id": context.id}), 201

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
        # Suppression du patch inutile sur full_data
        if not full_data or not isinstance(full_data, dict) or not all(k in full_data for k in ["title", "description", "skills", "responsibilities", "qualifications", "required_experience_years", "required_degree"]):
            logger.error(f"Fiche de poste LLM invalide ou vide : {full_data}")
            return jsonify({"error": "La génération de la fiche de poste a échoué. Veuillez réessayer ou modifier les paramètres."}), 502
        brief = JobBrief(
            title=data["title"],
            skills=json.dumps(data.get("skills", [])),
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
def list_briefs_user():
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
                    # Suppression du patch inutile sur full_description
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
        logger.info(f"Récupération des candidats pour l'utilisateur {current_user_id}")
        candidates = Candidate.query.filter_by(user_id=current_user_id).all()
        logger.info(f"Nombre de candidats trouvés: {len(candidates)}")
        
        candidates_data = []
        for c in candidates:
            # Correction parsing interview_questions, score_details, risks, recommendations
            questions = c.interview_questions
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except Exception:
                    questions = []
            elif questions is None:
                questions = []
                
            # Parsing score_details
            score_details = c.score_details
            if isinstance(score_details, str):
                try:
                    score_details = json.loads(score_details)
                except Exception:
                    score_details = {}
            elif score_details is None:
                score_details = {}
                
            # Parsing risks - gestion des types PostgreSQL JSON
            risks = c.risks
            if isinstance(risks, str):
                try:
                    risks = json.loads(risks)
                except Exception:
                    risks = []
            elif risks is None:
                risks = []
            # Si c'est déjà une liste/dict (PostgreSQL JSON), on la garde telle quelle
            elif not isinstance(risks, list):
                risks = []
                
            # Parsing recommendations - gestion des types PostgreSQL JSON
            recommendations = c.recommendations
            if isinstance(recommendations, str):
                try:
                    recommendations = json.loads(recommendations)
                except Exception:
                    recommendations = []
            elif recommendations is None:
                recommendations = []
            # Si c'est déjà une liste/dict (PostgreSQL JSON), on la garde telle quelle
            elif not isinstance(recommendations, list):
                recommendations = []
                
            candidates_data.append({
                "id": c.id,
                "name": c.name,
                "cv_analysis": json.loads(c.cv_analysis) if c.cv_analysis else None,
                "predictive_score": c.predictive_score,
                "status": c.status,
                "brief_id": c.brief_id,
                "user_id": c.user_id,
                "score_details": score_details,  # <-- Objet parsé
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
                "risks": risks,  # <-- Liste parsée
                "recommendations": recommendations  # <-- Liste parsée
            })
        return jsonify(candidates_data), 200
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des candidats: {str(e)}")
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
@bp.route('/api/cv/upload', methods=['POST'])
@jwt_required()
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
def upload_cv():
    try:
        logger.info(f"Upload CV - Requête POST reçue de {request.remote_addr}")
        logger.info(f"Upload CV - Headers: {dict(request.headers)}")
        logger.info(f"Upload CV - Files: {list(request.files.keys())}")
        logger.info(f"Upload CV - Form data: {dict(request.form)}")
        
        current_user_id = get_jwt_identity()
        logger.info(f"Upload CV - User ID: {current_user_id}")
        
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier fourni"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
        # Récupérer le brief_id depuis les données du formulaire (optionnel)
        brief_id = request.form.get('brief_id')
        if brief_id:
            # Vérifier que le brief appartient à l'utilisateur connecté
            brief = JobBrief.query.filter_by(id=brief_id, user_id=current_user_id).first()
            if not brief:
                return jsonify({"error": "Brief non trouvé ou non autorisé"}), 404
        else:
            # Utiliser le premier brief de l'utilisateur si aucun brief_id n'est spécifié
            brief = JobBrief.query.filter_by(user_id=current_user_id).first()
            if not brief:
                return jsonify({"error": "Aucun brief trouvé pour cet utilisateur"}), 404
            brief_id = brief.id
        
        # Sauvegarder le fichier
        file_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(file_path)
        
        # Extraire le texte du PDF
        cv_text = extract_text_from_pdf(file_path)
        if cv_text.startswith("Erreur"):
            return jsonify({"error": cv_text}), 400
        
        # Analyser le CV
        cv_data = analyze_cv(cv_text)
        if "error" in cv_data:
            return jsonify(cv_data), 500
        
        # Récupérer les détails du poste
        job_desc = json.loads(brief.full_data) if isinstance(brief.full_data, str) else brief.full_data
        
        # Ancien système pour rétrocompatibilité
        score_result = calculate_cv_score(cv_data, job_desc)
        visualize_scores(score_result)
        report = generate_final_report(cv_text, cv_data, score_result, job_desc)
        if "error" in report:
            return jsonify(report), 500
        
        # Créer le candidat avec un système simplifié
        candidate = Candidate(
            name=file.filename.split('.')[0],
            cv_analysis=json.dumps(cv_data),
            
            # Scores de base depuis score_result
            skills_score=score_result.get('skills_score', 0),
            experience_score=score_result.get('experience_score', 0),
            education_score=score_result.get('education_score', 0),
            culture_score=0.0,  # Sera calculé plus tard
            interview_score=0.0,  # Sera calculé plus tard
            final_predictive_score=0.0,  # Sera calculé APRÈS l'évaluation finale
            
            # Ancien système (rétrocompatibilité)
            predictive_score=score_result.get('final_score', 0),
            
            # Métadonnées
            status="CV analysé",
            process_stage="cv_analysis",
            brief_id=brief_id,
            user_id=current_user_id,
            
            # Données détaillées
            score_details=json.dumps(score_result),
            recommendations=json.dumps(report.get('recommendations', [])),
            risks=json.dumps(report.get('risks', []))
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        logger.info(f"🎯 Candidat créé - ID: {candidate.id}, Score final: {score_result.get('final_score', 0):.1f}%")
        logger.info(f"   Skills: {score_result.get('skills_score', 0):.1f}% | Experience: {score_result.get('experience_score', 0):.1f}% | Education: {score_result.get('education_score', 0):.1f}%")
        
        logger.info(f"Candidat créé avec succès - ID: {candidate.id}, nom: {candidate.name}, brief_id: {candidate.brief_id}")
        
        # Préparer la réponse avec la structure attendue par le frontend
        candidate_response = {
            "id": candidate.id,
            "name": candidate.name,
            "cv_analysis": cv_data,  # Déjà un dict, pas besoin de parser
            "predictive_score": candidate.predictive_score,
            "status": candidate.status,
            "brief_id": candidate.brief_id,
            "score_details": score_result,  # Déjà un dict, pas besoin de parser
            "report_summary": report.get('summary', ''),
            "recommendations": report.get('recommendations', []),
            "risks": report.get('risks', [])
        }
        
        response_data = {
            "message": "CV analysé avec succès",
            "candidate": candidate_response,
            "success": True
        }
        
        logger.info(f"Réponse d'upload envoyée: {json.dumps(candidate_response, indent=2)}")
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du CV: {str(e)}")
        return jsonify({"error": "Erreur lors de l'analyse du CV", "details": str(e)}), 500

# Route OPTIONS explicite pour l'upload de CV
@bp.route('/api/cv/upload', methods=['OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
def upload_cv_options():
    logger.info("Requête OPTIONS reçue pour /api/cv/upload")
    return '', 200

@bp.route('/api/cv/scores', methods=['GET'])
def get_cv_scores():
    return send_file("cv_scores.png", mimetype='image/png')


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
    
    # Préparer les appréciations pour l'analyse prédictive
    appreciations_for_analysis = []
    for app in appreciations:
        appreciations_for_analysis.append({
            "question": app['question'],
            "category": app['category'],
            "appreciation": app['appreciation'],
            "score": app['score']
        })
    
    analysis = generate_predictive_analysis(job_desc, cv_data, score_result, questions, appreciations_for_analysis)
    if "error" in analysis:
        return jsonify(analysis), 500
    
    # Sauvegarder les risques et recommandations générées
    candidate.risks = json.dumps(analysis.get('risks', []))
    candidate.recommendations = json.dumps(analysis.get('recommendations', []))
    candidate.predictive_score = analysis['predictive_score']
    candidate.status = "Évalué"
    db.session.commit()
    return jsonify({"message": "Évaluation soumise", "analysis": analysis}), 201

@bp.route('/api/evaluation/radar', methods=['GET'])
def get_radar():
    return send_file("predictive_radar.png", mimetype='image/png')

@bp.route('/api/candidates', methods=['GET'])
@jwt_required()
def get_candidates_api():
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"API - Récupération des candidats pour l'utilisateur {current_user_id}")
        candidates = Candidate.query.filter_by(user_id=current_user_id).all()
        logger.info(f"API - Nombre de candidats trouvés: {len(candidates)}")
        
        candidates_data = []
        for c in candidates:
            # Parsing score_details
            score_details = c.score_details
            if isinstance(score_details, str):
                try:
                    score_details = json.loads(score_details)
                except Exception:
                    score_details = {}
            elif score_details is None:
                score_details = {}
            
            # S'assurer que les scores directs sont inclus dans score_details
            if not score_details:
                score_details = {}
            
            # Construire les score_details à partir des colonnes individuelles de la base
            # Ceci remplace les valeurs obsolètes stockées en JSON par les vraies valeurs
            if hasattr(c, 'skills_score') and c.skills_score is not None:
                score_details['skills_score'] = c.skills_score
            if hasattr(c, 'experience_score') and c.experience_score is not None:
                score_details['experience_score'] = c.experience_score
            if hasattr(c, 'education_score') and c.education_score is not None:
                score_details['education_score'] = c.education_score
            if c.culture_score is not None:
                score_details['culture_score'] = c.culture_score
            if c.interview_score is not None:
                score_details['interview_score'] = c.interview_score
            
            # Parsing risks
            risks = c.risks
            if isinstance(risks, str):
                try:
                    risks = json.loads(risks)
                except Exception:
                    risks = []
            elif risks is None:
                risks = []
                
            # Parsing recommendations
            recommendations = c.recommendations
            if isinstance(recommendations, str):
                try:
                    recommendations = json.loads(recommendations)
                except Exception:
                    recommendations = []
            elif recommendations is None:
                recommendations = []
            
            candidates_data.append({
                "id": c.id,
                "name": c.name,
                "cv_analysis": json.loads(c.cv_analysis) if c.cv_analysis else None,
                "predictive_score": c.predictive_score,
                "status": c.status,
                "brief_id": c.brief_id,
                "user_id": c.user_id,
                "culture_score": c.culture_score,
                "interview_score": c.interview_score,
                "score_details": score_details,
                "risks": risks,
                "recommendations": recommendations,
                "appreciations": [{"question": a.question, "category": a.category, "appreciation": a.appreciation, "score": a.score} for a in c.appreciations]
            })
        
        logger.info(f"API - Candidats retournés: {len(candidates_data)}")
        
        # Log détaillé des scores pour debug
        for candidate_data in candidates_data:
            logger.info(f"API - Candidat {candidate_data['name']} - Culture: {candidate_data.get('culture_score')}, Interview: {candidate_data.get('interview_score')}, Score details: {candidate_data.get('score_details')}")
        
        return jsonify(candidates_data), 200
    except Exception as e:
        logger.error(f"API - Erreur lors de la récupération des candidats: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

# NOUVELLE API: Candidats avec système de scoring avancé
@bp.route('/api/v2/candidates', methods=['GET'])
@jwt_required()
def get_candidates_v2():
    """
    API v2 pour récupérer les candidats avec le système de scoring à 5 dimensions
    """
    try:
        current_user_id = get_jwt_identity()
        brief_id = request.args.get('brief_id', type=int)
        process_stage = request.args.get('process_stage')
        
        # Construire la requête
        query = Candidate.query.filter_by(user_id=current_user_id)
        
        if brief_id:
            query = query.filter_by(brief_id=brief_id)
        
        if process_stage:
            query = query.filter_by(process_stage=process_stage)
        
        candidates = query.order_by(Candidate.final_predictive_score.desc()).all()
        
        # Enrichir les données candidat
        candidates_data = []
        for candidate in candidates:
            # Utiliser une méthode simple pour convertir en dict
            candidate_dict = {
                'id': candidate.id,
                'name': candidate.name,
                'status': candidate.status,
                'process_stage': candidate.process_stage,
                'brief_id': candidate.brief_id,
                'user_id': candidate.user_id,
                'skills_score': candidate.skills_score,
                'experience_score': candidate.experience_score,
                'education_score': candidate.education_score,
                'culture_score': candidate.culture_score,
                'interview_score': candidate.interview_score,
                'final_predictive_score': candidate.final_predictive_score,
                'predictive_score': candidate.predictive_score
            }
            
            # Ajouter des métadonnées simples
            if candidate.final_predictive_score >= 80:
                candidate_dict['recommendation'] = "Excellent candidat"
            elif candidate.final_predictive_score >= 60:
                candidate_dict['recommendation'] = "Bon candidat"
            else:
                candidate_dict['recommendation'] = "À revoir"
            
            candidate_dict['process_stage_label'] = candidate.process_stage.replace('_', ' ').title()
            
            candidates_data.append(candidate_dict)
        
        return jsonify({
            'candidates': candidates_data,
            'total': len(candidates_data),
            'brief_id': brief_id,
            'filters': {
                'process_stage': process_stage
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur API v2 candidats: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

@bp.route('/api/v2/candidates/<int:candidate_id>/advance-stage', methods=['POST'])
@jwt_required()
def advance_candidate_stage(candidate_id):
    """
    Faire avancer un candidat à l'étape suivante du processus
    """
    try:
        current_user_id = get_jwt_identity()
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Progression des étapes
        stage_progression = {
            'cv_analysis': 'interview_questions_generated',
            'interview_questions_generated': 'interview_evaluated', 
            'interview_evaluated': 'final_assessment'
        }
        
        next_stage = stage_progression.get(candidate.process_stage)
        if not next_stage:
            return jsonify({"error": "Candidat déjà à l'étape finale"}), 400
        
        candidate.process_stage = next_stage
        db.session.commit()
        
        return jsonify({
            "message": f"Candidat avancé à l'étape: {next_stage.replace('_', ' ').title()}",
            "new_stage": next_stage,
            "candidate": {
                'id': candidate.id,
                'name': candidate.name,
                'status': candidate.status,
                'process_stage': candidate.process_stage,
                'brief_id': candidate.brief_id,
                'user_id': candidate.user_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur advancement candidat: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

# Routes pour les questions d'entretien et l'évaluation finale

@bp.route('/api/candidates/<int:candidate_id>/generate-interview-questions', methods=['POST', 'OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
@jwt_required()
def generate_candidate_interview_questions(candidate_id):
    """Génère les questions d'entretien pour un candidat"""
    try:
        current_user_id = get_jwt_identity()
        
        # Récupérer le candidat
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Récupérer le brief associé
        brief = JobBrief.query.filter_by(id=candidate.brief_id).first()
        if not brief:
            return jsonify({"error": "Brief non trouvé"}), 404
        
        # Récupérer le contexte d'entreprise
        context = CompanyContext.query.filter_by(id=brief.context_id).first()
        context_data = {
            "nom_entreprise": context.nom_entreprise if context else "",
            "domaine": context.domaine if context else "",
            "culture": context.description_culture if context else "",
            "valeurs": json.loads(context.valeurs) if context and context.valeurs else []
        }
        
        # Préparer les données pour la génération
        cv_data = json.loads(candidate.cv_analysis) if candidate.cv_analysis else {}
        job_data = json.loads(brief.full_data) if brief.full_data else {}
        
        # Calculer ou récupérer les scores
        # Calculer le score final s'il n'existe pas déjà
        if candidate.final_predictive_score:
            calculated_final_score = candidate.final_predictive_score
        else:
            calculated_final_score = (
                (candidate.skills_score or 0) * 0.25 +
                (candidate.experience_score or 0) * 0.20 +
                (candidate.education_score or 0) * 0.15 +
                (candidate.culture_score or 0) * 0.20 +
                (candidate.interview_score or 0) * 0.20
            )
        
        score_result = {
            "skills_score": candidate.skills_score if candidate.skills_score else 0,
            "experience_score": candidate.experience_score if candidate.experience_score else 0,
            "education_score": candidate.education_score if candidate.education_score else 0,
            "culture_score": candidate.culture_score if candidate.culture_score else 0,
            "interview_score": candidate.interview_score if candidate.interview_score else 0,
            "final_score": calculated_final_score
        }
        
        # Générer les questions avec les bons paramètres
        questions = generate_interview_questions(job_data, cv_data, score_result)
        
        if "error" in questions:
            return jsonify(questions), 500
        
        # Sauvegarder les questions - s'assurer que c'est bien en JSON string
        if isinstance(questions, dict):
            candidate.interview_questions = json.dumps(questions)
        else:
            # Si c'est déjà une string JSON, l'utiliser directement
            candidate.interview_questions = questions
            
        candidate.process_stage = PROCESS_STAGES['INTERVIEW_QUESTIONS']
        candidate.status = CANDIDATE_STATUS['INTERVIEW_QUESTIONS_GENERATED']
        
        db.session.commit()
        
        logger.info(f"Questions d'entretien générées pour candidat {candidate_id}")
        
        return jsonify({
            "success": True,
            "questions": questions,
            "candidate_id": candidate_id,
            "status": candidate.status
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur génération questions candidat {candidate_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la génération des questions", "details": str(e)}), 500

@bp.route('/api/candidates/<int:candidate_id>/evaluate-interview', methods=['POST', 'OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
@jwt_required()
def evaluate_candidate_interview(candidate_id):
    """Évalue l'entretien d'un candidat et calcule les scores culture + entretien"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Récupérer le candidat
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Récupérer les évaluations
        evaluations = data.get('evaluations', [])
        if not evaluations:
            return jsonify({"error": "Aucune évaluation fournie"}), 400
        
        # Calculer les scores culture et entretien
        culture_scores = []
        interview_scores = []
        
        logger.info(f"Début calcul scores pour candidat {candidate_id}")
        
        for evaluation in evaluations:
            category = evaluation.get('category', '').lower()
            score = float(evaluation.get('score', 0))
            
            logger.info(f"Évaluation: catégorie='{category}', score={score}")
            
            if 'culture' in category or 'company' in category:
                culture_scores.append(score)
                logger.info(f"-> Ajouté à culture_scores: {score}")
            else:
                interview_scores.append(score)
                logger.info(f"-> Ajouté à interview_scores: {score}")
        
        logger.info(f"Culture scores: {culture_scores}")
        logger.info(f"Interview scores: {interview_scores}")
        
        # Calculer les moyennes
        culture_score = sum(culture_scores) / len(culture_scores) if culture_scores else 0
        interview_score = sum(interview_scores) / len(interview_scores) if interview_scores else 0
        
        logger.info(f"Moyennes calculées - Culture: {culture_score}, Interview: {interview_score}")
        
        # Convertir en pourcentage (les scores frontend sont sur une échelle de 1-4)
        # 1 = Très insatisfait, 2 = Insatisfait, 3 = Satisfait, 4 = Très satisfait
        culture_score_pct = ((culture_score - 1) / 3.0) * 100  # Normaliser de 1-4 vers 0-100
        interview_score_pct = ((interview_score - 1) / 3.0) * 100  # Normaliser de 1-4 vers 0-100
        
        logger.info(f"Pourcentages - Culture: {culture_score_pct}%, Interview: {interview_score_pct}%")
        
        # Mettre à jour le candidat
        candidate.culture_score = culture_score_pct
        candidate.interview_score = interview_score_pct
        candidate.process_stage = PROCESS_STAGES['INTERVIEW_EVALUATION']
        candidate.status = CANDIDATE_STATUS['INTERVIEW_EVALUATED']
        
        # Sauvegarder les évaluations détaillées
        for evaluation in evaluations:
            appreciation = Appreciation(
                candidate_id=candidate_id,
                question=evaluation.get('question', ''),
                category=evaluation.get('category', ''),
                appreciation=evaluation.get('appreciation', ''),
                score=float(evaluation.get('score', 0))
            )
            db.session.add(appreciation)
        
        db.session.commit()
        
        logger.info(f"Entretien évalué pour candidat {candidate_id} - Culture: {culture_score_pct:.1f}%, Interview: {interview_score_pct:.1f}%")
        
        return jsonify({
            "success": True,
            "candidate_id": candidate_id,
            "culture_score": culture_score_pct,
            "interview_score": interview_score_pct,
            "status": candidate.status,
            "next_action": "Calcul du score prédictif final disponible"
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur évaluation entretien candidat {candidate_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Erreur lors de l'évaluation", "details": str(e)}), 500

@bp.route('/api/candidates/<int:candidate_id>/finalize-evaluation', methods=['POST', 'OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
@jwt_required()
def finalize_candidate_evaluation(candidate_id):
    """Finalise l'évaluation d'un candidat et calcule le score prédictif final"""
    try:
        current_user_id = get_jwt_identity()
        
        # Récupérer le candidat
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Vérifier que l'entretien a été évalué
        if candidate.culture_score == 0 or candidate.interview_score == 0:
            return jsonify({"error": "L'entretien doit être évalué avant de finaliser"}), 400
        
        # Calculer le score prédictif final
        result = ProcessManager.calculate_final_predictive_score(candidate_id)
        
        if "error" in result:
            return jsonify(result), 500
        
        # Générer les recommandations et risques finaux
        final_score = result['final_score']
        recommendation_data = ProcessManager.get_recommendation_from_score(final_score)
        
        # Créer les données radar pour les 5 dimensions
        radar_data = {
            "Compétences": candidate.skills_score,
            "Expérience": candidate.experience_score,
            "Formation": candidate.education_score,
            "Culture": candidate.culture_score,
            "Entretien": candidate.interview_score
        }
        
        # Générer des risques basés sur les scores faibles
        risks = []
        if candidate.skills_score < 60:
            risks.append("Compétences techniques insuffisantes")
        if candidate.experience_score < 60:
            risks.append("Expérience professionnelle limitée")
        if candidate.education_score < 60:
            risks.append("Formation académique inadéquate")
        if candidate.culture_score < 60:
            risks.append("Inadéquation culturelle avec l'entreprise")
        if candidate.interview_score < 60:
            risks.append("Performance d'entretien décevante")
        
        # Mettre à jour avec les données finales
        candidate.recommendations = json.dumps(recommendation_data)
        candidate.risks = json.dumps(risks)
        candidate.radar_data = json.dumps(radar_data)
        
        # Déterminer le statut final basé sur le score prédictif
        if final_score >= SCORING_THRESHOLDS['EXCELLENT']:  # >= 80
            candidate.status = "Recommandé"
        elif final_score >= SCORING_THRESHOLDS['GOOD']:      # >= 60
            candidate.status = "En évaluation"
        else:  # < 60
            candidate.status = "À revoir"
        
        db.session.commit()
        
        logger.info(f"Évaluation finalisée pour candidat {candidate_id} - Score final: {final_score:.2f}%")
        
        return jsonify({
            "success": True,
            "candidate_id": candidate_id,
            "final_predictive_score": final_score,
            "predictive_score": final_score,  # Rétrocompatibilité
            "recommendation": recommendation_data,
            "recommendations": [recommendation_data],  # Format tableau pour le frontend
            "risks": risks,
            "radar_data": radar_data,
            "status": candidate.status,
            "all_scores": {
                "skills": candidate.skills_score,
                "experience": candidate.experience_score,
                "education": candidate.education_score,
                "culture": candidate.culture_score,
                "interview": candidate.interview_score
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur finalisation candidat {candidate_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la finalisation", "details": str(e)}), 500

# Routes OPTIONS pour CORS
@bp.route('/api/candidates/<int:candidate_id>/generate-interview-questions', methods=['OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
def generate_interview_questions_options(candidate_id):
    return '', 200

@bp.route('/api/candidates/<int:candidate_id>/evaluate-interview', methods=['OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
def evaluate_interview_options(candidate_id):
    return '', 200

@bp.route('/api/candidates/<int:candidate_id>/finalize-evaluation', methods=['OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["POST", "OPTIONS"]
)
def finalize_evaluation_options(candidate_id):
    return '', 200

@bp.route('/api/candidates/<int:candidate_id>', methods=['OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["DELETE", "GET", "OPTIONS"]
)
def candidate_options(candidate_id):
    return '', 200

# Route pour supprimer un candidat
@bp.route('/api/candidates/<int:candidate_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(
    supports_credentials=True,
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["DELETE", "OPTIONS"]
)
@jwt_required()
def delete_candidate_api(candidate_id):
    """Supprimer un candidat"""
    try:
        current_user_id = get_jwt_identity()
        
        # Récupérer le candidat
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Supprimer les appréciations associées
        Appreciation.query.filter_by(candidate_id=candidate_id).delete()
        
        # Supprimer le candidat
        db.session.delete(candidate)
        db.session.commit()
        
        logger.info(f"Candidat {candidate_id} supprimé avec succès")
        
        return jsonify({
            "success": True,
            "message": "Candidat supprimé avec succès",
            "candidate_id": candidate_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur suppression candidat {candidate_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression", "details": str(e)}), 500

# Route pour récupérer un candidat spécifique
@bp.route('/api/candidates/<int:candidate_id>', methods=['GET'])
@jwt_required()
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["GET", "OPTIONS"]
)
def get_candidate_by_id_api(candidate_id):
    """Récupérer un candidat spécifique"""
    try:
        current_user_id = get_jwt_identity()
        
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Parsing des données JSON
        cv_analysis = json.loads(candidate.cv_analysis) if candidate.cv_analysis else None
        score_details = json.loads(candidate.score_details) if candidate.score_details else {}
        interview_questions = json.loads(candidate.interview_questions) if candidate.interview_questions else []
        recommendations = json.loads(candidate.recommendations) if candidate.recommendations else []
        risks = json.loads(candidate.risks) if candidate.risks else []
        
        candidate_data = {
            "id": candidate.id,
            "name": candidate.name,
            "cv_analysis": cv_analysis,
            "predictive_score": candidate.predictive_score,
            "status": candidate.status,
            "process_stage": candidate.process_stage,
            "brief_id": candidate.brief_id,
            "user_id": candidate.user_id,
            
            # Scores détaillés
            "skills_score": candidate.skills_score,
            "experience_score": candidate.experience_score,
            "education_score": candidate.education_score,
            "culture_score": candidate.culture_score,
            "interview_score": candidate.interview_score,
            "final_predictive_score": candidate.final_predictive_score,
            
            # Données détaillées
            "score_details": score_details,
            "interview_questions": interview_questions,
            "recommendations": recommendations,
            "risks": risks,
            
            # Appréciations
            "appreciations": [
                {
                    "id": a.id,
                    "candidate_id": a.candidate_id,
                    "question": a.question,
                    "category": a.category,
                    "appreciation": a.appreciation,
                    "score": a.score
                }
                for a in candidate.appreciations
            ] if candidate.appreciations else []
        }
        
        return jsonify(candidate_data), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération candidat {candidate_id}: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500

@bp.route('/api/candidates/<int:candidate_id>/interview-questions', methods=['GET', 'OPTIONS'])
@cross_origin(
    supports_credentials=True, 
    origins=["http://localhost:8080", "https://technova-frontend.vercel.app"], 
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    methods=["GET", "OPTIONS"]
)
@jwt_required()
def get_candidate_interview_questions(candidate_id):
    """Récupère les questions d'entretien existantes pour un candidat"""
    try:
        current_user_id = get_jwt_identity()
        
        # Récupérer le candidat
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=current_user_id).first()
        if not candidate:
            return jsonify({"error": "Candidat non trouvé"}), 404
        
        # Vérifier si des questions existent
        if not candidate.interview_questions:
            return jsonify({"error": "Aucune question d'entretien trouvée pour ce candidat"}), 404
        
        # Récupérer les questions - gérer le cas où c'est déjà un dict ou une string JSON
        try:
            if isinstance(candidate.interview_questions, str):
                questions = json.loads(candidate.interview_questions)
            else:
                # Si c'est déjà un dict (cas d'erreur de sauvegarde précédente)
                questions = candidate.interview_questions
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON questions candidat {candidate_id}: {str(e)}")
            return jsonify({"error": "Erreur de format des questions stockées"}), 500
        
        logger.info(f"Questions d'entretien récupérées pour candidat {candidate_id}")
        
        return jsonify({
            "success": True,
            "questions": questions,
            "candidate_id": candidate_id,
            "status": candidate.status
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération questions candidat {candidate_id}: {str(e)}")
        return jsonify({"error": "Erreur lors de la récupération des questions", "details": str(e)}), 500
