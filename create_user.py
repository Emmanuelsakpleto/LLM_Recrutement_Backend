from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User(username='admin', email='admin@example.com')
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    print('Utilisateur créé avec succès!')
