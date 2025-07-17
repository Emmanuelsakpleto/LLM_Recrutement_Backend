from . import db
from datetime import datetime
import json

class JobBrief(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    full_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    context_id = db.Column(db.Integer, db.ForeignKey('company_context.id'), nullable=True)
    
    def to_dict(self):
        # Gestion sécurisée du parsing des skills
        skills_parsed = []
        if self.skills:
            try:
                if isinstance(self.skills, str):
                    skills_parsed = json.loads(self.skills)
                else:
                    skills_parsed = self.skills
            except (json.JSONDecodeError, TypeError):
                # Si le parsing échoue, on traite comme une chaîne simple
                skills_parsed = [self.skills] if self.skills else []
        
        # Gestion sécurisée du parsing de full_data
        full_data_parsed = None
        if self.full_data:
            try:
                if isinstance(self.full_data, str):
                    full_data_parsed = json.loads(self.full_data)
                else:
                    full_data_parsed = self.full_data
            except (json.JSONDecodeError, TypeError):
                full_data_parsed = None
        
        return {
            'id': self.id,
            'title': self.title,
            'skills': skills_parsed,
            'experience': self.experience,
            'description': self.description,
            'full_data': full_data_parsed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status
        }

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cv_analysis = db.Column(db.Text)  # JSON string
    
    # Score prédictif simple (pour rétrocompatibilité)
    predictive_score = db.Column(db.Float, default=0.0)
    
    # Les 5 scores détaillés
    skills_score = db.Column(db.Float, default=0.0)
    experience_score = db.Column(db.Float, default=0.0)
    education_score = db.Column(db.Float, default=0.0)
    culture_score = db.Column(db.Float, default=0.0)
    interview_score = db.Column(db.Float, default=0.0)
    
    # Score prédictif final (combinaison des 5 scores)
    final_predictive_score = db.Column(db.Float, default=0.0)
    
    # Métadonnées
    status = db.Column(db.String(50), nullable=False)
    process_stage = db.Column(db.String(50), default='cv_analysis')
    brief_id = db.Column(db.Integer, db.ForeignKey('job_brief.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Données détaillées (JSON)
    interview_questions = db.Column(db.Text)  # JSON string
    score_details = db.Column(db.Text)  # JSON string
    risks = db.Column(db.Text)  # JSON string
    recommendations = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convertit le candidat en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'name': self.name,
            'cv_analysis': json.loads(self.cv_analysis) if self.cv_analysis else None,
            'predictive_score': self.predictive_score,
            'final_predictive_score': self.final_predictive_score,
            'scores': {
                'skills': self.skills_score,
                'experience': self.experience_score,
                'education': self.education_score,
                'culture': self.culture_score,
                'interview': self.interview_score
            },
            'status': self.status,
            'process_stage': self.process_stage,
            'brief_id': self.brief_id,
            'user_id': self.user_id,
            'score_details': json.loads(self.score_details) if self.score_details else {},
            'risks': json.loads(self.risks) if self.risks else [],
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CompanyContext(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nom_entreprise = db.Column(db.String(200), nullable=True)
    domaine = db.Column(db.String(200), nullable=True)
    valeurs = db.Column(db.Text, nullable=False)
    description_culture = db.Column(db.Text, nullable=False)

class InterviewQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text)

class Appreciation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    appreciation = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    candidate = db.relationship('Candidate', backref=db.backref('appreciations', lazy=True))

from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.username}>'