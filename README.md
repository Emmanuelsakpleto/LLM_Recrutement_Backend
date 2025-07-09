# TheRecruit – Backend

Backend Python/Flask robuste pour la plateforme de gestion de recrutement TheRecruit.

## Fonctionnalités principales

- API RESTful sécurisée (JWT)
- Gestion des briefs de poste, contextes d’entreprise, candidats, appréciations
- Analyse automatisée de CV et scoring prédictif
- Génération de questions d’entretien personnalisées
- Génération de rapports PDF (ReportLab)
- Logging avancé
- Migrations de base de données (Alembic)

## Stack technique

- Python 3
- Flask
- SQLAlchemy
- Flask-JWT-Extended
- Flask-CORS
- Alembic
- ReportLab

## Installation

### Prérequis
- Python >= 3.9
- PostgreSQL

### Démarrage rapide
```sh
git clone <repo>
cd TechNovaBackend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
flask run
```

## Commandes utiles

- Initialiser la base de données :
  ```sh
  flask init-db
  ```
- Lancer le serveur :
  ```sh
  flask run
  ```

## Structure du projet

- `app/` : code principal (routes, modèles, modules, utilitaires)
- `migrations/` : scripts de migration Alembic
- `run.py` : point d’entrée de l’application
- `requirements.txt` : dépendances Python

