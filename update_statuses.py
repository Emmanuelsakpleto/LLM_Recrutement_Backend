#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Candidate

def update_candidate_statuses():
    """Met à jour les statuts des candidats existants basés sur leurs scores"""
    
    app = create_app()
    
    with app.app_context():
        # Récupérer tous les candidats avec un score prédictif final
        candidates = Candidate.query.filter(Candidate.final_predictive_score.isnot(None)).all()
        
        print(f"🔄 Mise à jour de {len(candidates)} candidats...")
        
        for candidate in candidates:
            old_status = candidate.status
            final_score = candidate.final_predictive_score
            
            # Déterminer le nouveau statut
            if final_score >= 80:  # Excellent
                new_status = "Recommandé"
            elif final_score >= 60:  # Bon
                new_status = "En évaluation"
            else:  # À revoir
                new_status = "À revoir"
            
            # Mettre à jour le statut
            candidate.status = new_status
            
            print(f"👤 {candidate.name}")
            print(f"   📈 Score: {final_score:.1f}%")
            print(f"   📌 Statut: '{old_status}' → '{new_status}'")
            print()
        
        # Sauvegarder les changements
        db.session.commit()
        print("✅ Statuts mis à jour avec succès!")
        
        # Vérification
        print("\n📊 Résumé après mise à jour:")
        statuses = {}
        for candidate in candidates:
            status = candidate.status
            statuses[status] = statuses.get(status, 0) + 1
        
        for status, count in statuses.items():
            print(f"   • {status}: {count} candidat(s)")

if __name__ == "__main__":
    update_candidate_statuses()
