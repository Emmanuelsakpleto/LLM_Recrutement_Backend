from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import jwt
from functools import wraps
from . import db
from .models import User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        
        try:
            token = token.split()[1]  # Enlever le préfixe "Bearer"
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Token invalide'}), 401
        except:
            return jsonify({'message': 'Token invalide'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@bp.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({
            "message": "Le Content-Type doit être application/json"
        }), 415
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "Corps de la requête vide"}), 400
        
        # Validation des champs requis
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"message": f"Le champ {field} est requis"}), 400
        
        # Vérification si l'email existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"message": "Cet email est déjà utilisé"}), 409
        
        # Vérification si le username existe déjà
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"message": "Ce nom d'utilisateur est déjà utilisé"}), 409
        
        # Création du nouvel utilisateur
        new_user = User(
            username=data['username'],
            email=data['email'],
            role='user'  # Par défaut
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "message": "Utilisateur créé avec succès",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "Erreur lors de la création de l'utilisateur",
            "error": str(e)
        }), 500

@bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"message": "Le Content-Type doit être application/json"}), 415
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "Corps de la requête vide"}), 400
        
        # Validation des champs requis
        if not data.get('email') or not data.get('password'):
            return jsonify({"message": "Email et mot de passe requis"}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({"message": "Email ou mot de passe incorrect"}), 401
        
        # Mise à jour du dernier login
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        db.session.commit()
        
        # Génération du token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, current_app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            "message": "Connexion réussie",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la connexion: {str(e)}")
        return jsonify({
            "message": "Erreur lors du traitement de la requête",
            "error": str(e)
        }), 500

@bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })
