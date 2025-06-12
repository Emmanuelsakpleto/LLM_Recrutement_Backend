import os
import logging
from flask import Blueprint, request, jsonify, send_file
from . import db
from .models import JobBrief, CompanyContext, InterviewQuestion, Candidate, Appreciation, User
from .modules.llms import generate_job_description, extract_text_from_pdf, analyze_cv, calculate_cv_score, visualize_scores, generate_final_report, generate_interview_questions, generate_predictive_analysis
import json
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

bp = Blueprint('routes', __name__)

@bp.route('/api/job-briefs', methods=['POST'])
def create_brief():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400

        # Validation des champs requis
        required_fields = ['title', 'skills', 'experience', 'description']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "error": f"Champs manquants : {', '.join(missing_fields)}"
            }), 400

        try:
            # Tentative de génération de description avec l'IA
            description = generate_job_description(data)
            if not description:
                # Si la génération échoue, utiliser la description fournie
                description = data['description']
        except Exception as e:
            # En cas d'erreur avec l'IA, utiliser la description fournie
            description = data['description']

        # S'assurer que nous avons une description
        if not description:
            return jsonify({
                "error": "Impossible de créer une fiche sans description"
            }), 400

        # Conversion du dictionnaire en JSON string
        full_data_json = json.dumps(data)        # S'assurer que skills est au format JSON string
        skills_json = json.dumps(data['skills']) if isinstance(data['skills'], list) else data['skills']
        
        brief = JobBrief(
            title=data['title'],
            skills=skills_json,
            experience=data['experience'],
            description=description,  # Description garantie non-null
            full_data=full_data_json
        )

        db.session.add(brief)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Fiche de poste créée",
            "data": brief.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Erreur lors de la création",
            "details": str(e)
        }), 500

# Supprimer cette route qui fait doublon
# @bp.route('/api/job-briefs', methods=['GET'])
# def get_brief():
#     brief = JobBrief.query.first()
#     if not brief:
#         return jsonify({"message": "Aucun brief trouvé"}), 404
#     return jsonify(json.loads(brief.full_data))

@bp.route('/api/job-briefs/<int:brief_id>', methods=['GET'])
def get_brief_by_id(brief_id):  # Renommé la fonction
    """Récupérer une fiche de poste spécifique"""
    try:
        brief = JobBrief.query.get(brief_id)
        if not brief:
            return jsonify({
                "error": "Fiche de poste non trouvée",
                "brief_id": brief_id
            }), 404
            
        return jsonify({
            "status": "success",
            "data": brief.to_dict()
        }), 200
        
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
