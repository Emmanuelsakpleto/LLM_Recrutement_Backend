#!/usr/bin/env python3
"""
Script pour corriger le format des questions d'entretien dans la base de données
"""

import json
import sys
import os

# Ajouter le répertoire racine au path pour importer l'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Candidate

def fix_interview_questions():
    """Corrige le format des questions d'entretien stockées"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Recherche des candidats avec des questions d'entretien...")
        
        candidates = Candidate.query.filter(Candidate.interview_questions.isnot(None)).all()
        print(f"📊 {len(candidates)} candidats trouvés avec des questions")
        
        fixed_count = 0
        
        for candidate in candidates:
            try:
                print(f"\n--- Candidat ID: {candidate.id} ---")
                print(f"Nom: {candidate.name}")
                print(f"Type actuel: {type(candidate.interview_questions)}")
                
                # Si c'est déjà une string, essayer de la parser pour vérifier
                if isinstance(candidate.interview_questions, str):
                    try:
                        parsed = json.loads(candidate.interview_questions)
                        print("✅ Format JSON string correct")
                        continue
                    except json.JSONDecodeError:
                        print("❌ String JSON invalide, conversion nécessaire")
                
                # Si c'est un dict, le convertir en string JSON
                elif isinstance(candidate.interview_questions, dict):
                    print("🔧 Conversion dict -> JSON string")
                    candidate.interview_questions = json.dumps(candidate.interview_questions)
                    fixed_count += 1
                    
                else:
                    print(f"❓ Type non reconnu: {type(candidate.interview_questions)}")
                    
            except Exception as e:
                print(f"❌ Erreur pour candidat {candidate.id}: {str(e)}")
        
        if fixed_count > 0:
            print(f"\n💾 Sauvegarde de {fixed_count} corrections...")
            db.session.commit()
            print("✅ Corrections appliquées avec succès!")
        else:
            print("\n✅ Aucune correction nécessaire")
        
        print(f"\n📈 Résumé: {fixed_count} candidats corrigés sur {len(candidates)} total")

if __name__ == "__main__":
    fix_interview_questions()
