from app import create_app, db
from app.models import User
import traceback

app = create_app()

def test_db_connection():
    try:
        with app.app_context():
            # Test la connexion en effectuant une requête simple
            User.query.first()
            print("✅ Connexion à la base de données réussie !")
    except Exception as e:
        print("❌ Erreur de connexion à la base de données:")
        print(str(e))
        print("\nTraceback complet:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_db_connection()
