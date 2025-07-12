from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config
import logging

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configuration CORS sécurisée
    CORS(app,
        resources={r"/*": {
            "origins": ["http://localhost:8080", "https://technova-frontend.vercel.app"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
            "supports_credentials": True,
            "expose_headers": ["Content-Range", "X-Total-Count"]
        }},
        supports_credentials=True)
    
    with app.app_context():
        from . import models
        from .routes import bp as routes_bp
        from .auth import auth_bp
        
        # Enregistrement des blueprints avec préfixes
        app.register_blueprint(routes_bp)  # Pas de préfixe si routes_bp n'en a pas besoin
        app.register_blueprint(auth_bp, url_prefix='/api')  # Ajoute le préfixe ici
        db.create_all()

    return app