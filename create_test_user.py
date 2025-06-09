from app import create_app, db
from app.models import User

def create_test_user():
    app = create_app()
    with app.app_context():
        # Vérifier si l'utilisateur existe déjà
        if not User.query.filter_by(email='test@technova.fr').first():
            user = User(
                username='test',
                email='test@technova.fr',
                role='admin'
            )
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
            print("Utilisateur test créé avec succès!")
        else:
            print("L'utilisateur test existe déjà!")

if __name__ == '__main__':
    create_test_user()
