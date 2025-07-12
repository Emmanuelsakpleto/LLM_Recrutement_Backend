from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.info('Inscription tentée: %s', data)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'Tous les champs sont requis'}), 400

        existing_user = User.query.with_entities(User.id, User.username, User.email, User.password).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            return jsonify({'error': 'Email ou nom d\'utilisateur déjà utilisé'}), 400

        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        logger.info('Inscription réussie pour %s', username)

        return jsonify({
            'message': 'Inscription réussie',
            'user': {'id': user.id, 'username': user.username, 'email': user.email}
        }), 201
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur', 'details': str(e)}), 500
    

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        # Utiliser une requête explicite sans colonnes manquantes
        user = User.query.with_entities(User.id, User.username, User.email, User.password).filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

        access_token = create_access_token(identity=str(user.id))
        logger.info('Connexion réussie pour %s', email)  # Remplace app.logger par logger

        return jsonify({
            'message': 'Connexion réussie',
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}")  # Remplace app.logger par logger
        return jsonify({
            "error": "Erreur lors de la connexion",
            "details": str(e)
        }), 500