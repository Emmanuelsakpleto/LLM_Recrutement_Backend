from app import create_app, db
from app.models import User, JobBrief, CompanyContext, InterviewQuestion
import json
import click
from flask.cli import with_appcontext

def init_db():
    """Initialise la base de données"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ Base de données initialisée !")

def create_admin():
    """Crée l'utilisateur administrateur"""
    app = create_app()
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='recruteur@technova.com',
                role='admin'
            )
            admin.set_password('TechNova2025')
            db.session.add(admin)
            db.session.commit()
            print("✓ Utilisateur admin créé avec succès")
        else:
            print("ℹ L'utilisateur admin existe déjà")

def seed_test_data():
    """Ajoute des données de test dans la base de données"""
    app = create_app()
    with app.app_context():
        # Exemple de fiche de poste
        if not JobBrief.query.first():
            example_brief = JobBrief(
                title="Développeur Python Senior",
                skills=json.dumps(["Python", "Flask", "SQL", "API REST", "Docker"]),
                experience=5,
                description="Développeur Python expérimenté pour notre équipe backend",
                full_data=json.dumps({
                    "title": "Développeur Python Senior",
                    "description": "Nous recherchons un développeur Python expérimenté pour rejoindre notre équipe backend dynamique.",
                    "skills": ["Python", "Flask", "SQL", "API REST", "Docker"],
                    "responsibilities": [
                        "Développement d'APIs REST",
                        "Conception de bases de données",
                        "Mise en place de tests automatisés"
                    ],
                    "qualifications": [
                        "5 ans d'expérience en développement Python",
                        "Maîtrise des frameworks web modernes",
                        "Expérience avec les bases de données SQL"
                    ],
                    "required_experience_years": 5,
                    "required_degree": "Master"
                })
            )
            db.session.add(example_brief)
            print("✓ Fiche de poste exemple créée")

        # Contexte d'entreprise
        if not CompanyContext.query.first():
            context = CompanyContext(
                values=json.dumps([
                    "Innovation",
                    "Collaboration",
                    "Excellence technique",
                    "Impact client"
                ]),
                culture="TechNova est une startup SaaS innovante qui valorise la collaboration, la transparence et l'impact client."
            )
            db.session.add(context)
            print("✓ Contexte d'entreprise créé")

        # Questions d'entretien exemple
        if not InterviewQuestion.query.first():
            example_questions = [
                {
                    "question": "Décrivez un projet technique complexe que vous avez géré.",
                    "category": "Expérience Technique",
                    "purpose": "Évaluer la capacité à gérer des projets complexes"
                },
                {
                    "question": "Comment gérez-vous les conflits dans une équipe ?",
                    "category": "Soft Skills",
                    "purpose": "Évaluer les compétences interpersonnelles"
                }
            ]
            for q in example_questions:
                question = InterviewQuestion(
                    question=q["question"],
                    category=q["category"],
                    purpose=q["purpose"]
                )
                db.session.add(question)
            print("✓ Questions d'entretien exemple créées")

        db.session.commit()
        print("\n✓ Données de test ajoutées avec succès !")

def reset_db():
    """Réinitialise la base de données (supprime et recrée)"""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Base de données réinitialisée !")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_db()
        elif command == "create-admin":
            create_admin()
        elif command == "seed":
            seed_test_data()
        elif command == "reset":
            reset_db()
        elif command == "setup-all":
            reset_db()
            create_admin()
            seed_test_data()
    else:
        print("Usage: python db_manager.py [command]")
        print("Commands disponibles:")
        print("  init         : Initialise la base de données")
        print("  create-admin : Crée l'utilisateur admin")
        print("  seed        : Ajoute des données de test")
        print("  reset       : Réinitialise la base de données")
        print("  setup-all   : Réinitialise et configure tout")
