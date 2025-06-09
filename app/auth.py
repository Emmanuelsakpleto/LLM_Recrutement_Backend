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
    # Vérification basique du Content-Type
    if not request.is_json:
        return jsonify({
            "message": "Le Content-Type doit être application/json",
            "received_headers": dict(request.headers)
        }), 415
    
    try:
        # Tentative de récupération des données JSON
        data = request.get_json()
        
        # Vérification des données requises
        if not data:
            return jsonify({"message": "Corps de la requête vide"}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email et password requis"}), 400
        
        # Recherche de l'utilisateur
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "Utilisateur non trouvé"}), 401
        
        # Vérification du mot de passe
        if not user.check_password(password):
            return jsonify({"message": "Mot de passe incorrect"}), 401
        
        # Génération du token JWT
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS'])
        }, current_app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.username,
                'role': user.role,
                'company': 'TechNova'  # Pour correspondre au mockUser
            }        }), 200
        
    except Exception as e:
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
