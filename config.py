import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # S'assurer que le dossier instance existe
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Configuration de la base de données
    db_path = os.path.join(instance_path, 'database.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    # Configuration CORS
    CORS_HEADERS = ['Content-Type', 'Authorization', 'Access-Control-Allow-Origin', 'Accept']
    CORS_ORIGINS = [
        "http://localhost:3000",     # Pour le développement React
        "http://localhost:5173",     # Pour le développement Vite
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8081",     # Pour Expo
        "http://10.0.2.2:8081",     # Pour l'émulateur Android
        "exp://localhost:8081",      # Pour Expo en développement
        "exp://10.0.2.2:8081",      # Pour Expo sur émulateur Android
        "http://10.0.2.2:19000",    # Pour l'émulateur Android
        "http://10.0.2.2:19001",    # Pour l'émulateur Android
        "http://10.0.2.2:19002",    # Pour l'émulateur Android
        "http://10.0.2.2:5000",     # Pour l'accès direct à l'API
        "http://localhost:5000",     # Pour les tests locaux
        "http://127.0.0.1:5000",    # Pour les tests locaux
        "exp://192.168.*.*:*",      # Pour le réseau local
        "http://192.168.*.*:*",     # Pour le réseau local
        "*"                         # En développement uniquement
    ]
    
    # Configuration CORS supplémentaire
    CORS_ALLOW_HEADERS = '*'
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization', 'Access-Control-Allow-Origin']
    CORS_MAX_AGE = 600  # 10 minutes
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-replace-in-production')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')