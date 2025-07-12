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
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'skills': json.loads(self.skills) if isinstance(self.skills, str) else self.skills,
            'experience': self.experience,
            'description': self.description,
            'full_data': json.loads(self.full_data) if self.full_data else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status
        }

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cv_analysis = db.Column(db.Text)  # JSON string
    predictive_score = db.Column(db.Float)
    status = db.Column(db.String(50), nullable=False)

class CompanyContext(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    values = db.Column(db.Text, nullable=False)
    culture = db.Column(db.Text, nullable=False)

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