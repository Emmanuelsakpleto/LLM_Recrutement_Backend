#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import os

def check_database_recommendations():
    """Vérifie les recommandations et risques dans la base de données"""
    
    # Chercher le fichier de base de données
    db_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite'):
                db_files.append(os.path.join(root, file))
    
    print(f"🔍 Fichiers de base de données trouvés: {db_files}")
    
    # Utiliser le premier fichier trouvé ou créer une connexion par défaut
    if db_files:
        db_path = db_files[0]
        print(f"📁 Utilisation de: {db_path}")
    else:
        db_path = 'instance/recruitment.db'  # Chemin par défaut
        print(f"📁 Tentative avec le chemin par défaut: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables trouvées: {[t[0] for t in tables]}")
        
        # Vérifier la structure de la table candidate
        cursor.execute("PRAGMA table_info(candidate);")
        columns = cursor.fetchall()
        print(f"🏗️ Colonnes de la table candidate:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Vérifier s'il y a des candidats
        cursor.execute("SELECT COUNT(*) FROM candidate;")
        count = cursor.fetchone()[0]
        print(f"👥 Nombre total de candidats: {count}")
        
        if count > 0:
            # Récupérer quelques candidats avec leurs risques et recommandations
            cursor.execute("""
                SELECT id, name, risks, recommendations, 
                       skills_score, experience_score, education_score, 
                       culture_score, interview_score, status
                FROM candidate 
                LIMIT 5;
            """)
            candidates = cursor.fetchall()
            
            print(f"\n📋 Détails des candidats:")
            for candidate in candidates:
                (id, name, risks, recommendations, skills_score, experience_score, 
                 education_score, culture_score, interview_score, status) = candidate
                
                print(f"\n🧑 Candidat ID {id}: {name}")
                print(f"   Status: {status}")
                print(f"   Scores: Skills={skills_score}, Exp={experience_score}, Edu={education_score}")
                print(f"   Culture={culture_score}, Interview={interview_score}")
                
                # Parser les risques
                if risks:
                    try:
                        parsed_risks = json.loads(risks)
                        print(f"   🚨 Risques: {len(parsed_risks)} éléments")
                        for i, risk in enumerate(parsed_risks, 1):
                            if isinstance(risk, dict):
                                print(f"      {i}. {risk.get('risk', risk.get('description', str(risk)))}")
                            else:
                                print(f"      {i}. {risk}")
                    except json.JSONDecodeError:
                        print(f"   🚨 Risques (brut): {risks[:100]}...")
                else:
                    print(f"   🚨 Risques: VIDES")
                
                # Parser les recommandations
                if recommendations:
                    try:
                        parsed_recs = json.loads(recommendations)
                        print(f"   💡 Recommandations: {len(parsed_recs)} éléments")
                        for i, rec in enumerate(parsed_recs, 1):
                            if isinstance(rec, dict):
                                print(f"      {i}. {rec.get('type', 'Type inconnu')}: {rec.get('description', str(rec))[:80]}...")
                            else:
                                print(f"      {i}. {rec}")
                    except json.JSONDecodeError:
                        print(f"   💡 Recommandations (brut): {recommendations[:100]}...")
                else:
                    print(f"   💡 Recommandations: VIDES")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'accès à la base de données: {str(e)}")

if __name__ == "__main__":
    check_database_recommendations()
