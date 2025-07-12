#!/usr/bin/env python3
"""Script de migration pour ajouter les nouveaux champs de scoring"""

from app import create_app, db
from sqlalchemy import text

def migrate_scoring_fields():
    app = create_app()
    with app.app_context():
        print("🔧 Début de la migration des champs de scoring...")
        
        try:
            # Ajouter les nouveaux champs un par un
            fields_to_add = [
                "ALTER TABLE candidate ADD COLUMN skills_score FLOAT DEFAULT 0.0",
                "ALTER TABLE candidate ADD COLUMN experience_score FLOAT DEFAULT 0.0", 
                "ALTER TABLE candidate ADD COLUMN education_score FLOAT DEFAULT 0.0",
                "ALTER TABLE candidate ADD COLUMN culture_score FLOAT DEFAULT 0.0",
                "ALTER TABLE candidate ADD COLUMN interview_score FLOAT DEFAULT 0.0",
                "ALTER TABLE candidate ADD COLUMN process_stage VARCHAR(50) DEFAULT 'cv_analysis'",
                "ALTER TABLE candidate ADD COLUMN final_predictive_score FLOAT DEFAULT 0.0"
            ]
            
            for sql in fields_to_add:
                try:
                    db.session.execute(text(sql))
                    field_name = sql.split("ADD COLUMN ")[1].split(" ")[0]
                    print(f"✅ Champ {field_name} ajouté")
                except Exception as e:
                    field_name = sql.split("ADD COLUMN ")[1].split(" ")[0] 
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠️  Champ {field_name} existe déjà")
                    else:
                        print(f"❌ Erreur pour {field_name}: {e}")
            
            db.session.commit()
            print("🎉 Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur globale: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_scoring_fields()
