import os
from app import create_app, db
from app.models import JobBrief, CompanyContext, InterviewQuestion, Candidate, Appreciation
from app.auth import auth_bp  # Importation toujours nécessaire pour charger le blueprint
from flask import jsonify, request, make_response
from flask_cors import cross_origin, CORS
import logging

app = create_app()

# Configuration globale de CORS (redondant avec create_app, peut être supprimé)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}})

# Configuration des headers CORS par défaut (redondant, peut être supprimé)
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Max-Age'] = '86400'
    return response

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Base de données initialisée !")

@app.before_request
def log_request_info():
    app.logger.info('Request received: %s %s', request.method, request.path)
    app.logger.info('Headers: %s', dict(request.headers))
    app.logger.info('Remote addr: %s', request.remote_addr)
    app.logger.info('Body: %s', request.get_data())

# Supprime ou commente cette ligne
# app.register_blueprint(auth_bp, url_prefix='/api', name='auth_v1')

@app.route('/api')
@app.route('/api/')
@cross_origin()
def index():
    app.logger.info('Requête reçue sur /api')
    return jsonify({
        "status": "API is running",
        "version": "1.0",
        "api_name": "TechNovaRH Backend",
        "request_headers": dict(request.headers),
        "debug_info": {
            "method": request.method,
            "origin": request.headers.get('Origin'),
            "host": request.headers.get('Host')
        }
    })

@app.route('/api/test-cors', methods=['OPTIONS', 'GET'])
@cross_origin()
def test_cors():
    if request.method == 'OPTIONS':
        response = jsonify({"status": "CORS preflight accepted"})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    return jsonify({"status": "CORS test successful", "received_headers": dict(request.headers)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)