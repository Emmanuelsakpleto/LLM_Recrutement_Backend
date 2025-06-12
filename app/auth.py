from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400

        # Validation des champs requis
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "error": f"Champs manquants : {', '.join(missing_fields)}"
            }), 400

        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email déjà utilisé"}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Nom d'utilisateur déjà utilisé"}), 400

        # Créer le nouvel utilisateur avec password au lieu de password_hash
        hashed_password = generate_password_hash(data['password'])
        user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password  # Utiliser password au lieu de password_hash
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Utilisateur créé avec succès",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        return jsonify({
            "error": "Erreur lors de l'inscription",
            "details": str(e)
        }), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Connexion d'un utilisateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400

        # Validation des champs requis
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email et mot de passe requis"}), 400

        # Vérifier les identifiants - utiliser password au lieu de password_hash
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({"error": "Identifiants invalides"}), 401

        # Créer le token JWT
        access_token = create_access_token(identity=user.id)

        return jsonify({
            "token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}")
        return jsonify({
            "error": "Erreur lors de la connexion",
            "details": str(e)
        }), 500

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Récupérer les informations de l'utilisateur connecté"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
        return jsonify({
            "error": "Erreur serveur",
            "details": str(e)
        }), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnexion (côté client principalement)"""
    try:
        # Dans une implémentation plus complexe, on pourrait blacklister le token
        return jsonify({"message": "Déconnexion réussie"}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        return jsonify({
            "error": "Erreur lors de la déconnexion",
            "details": str(e)
        }), 500
