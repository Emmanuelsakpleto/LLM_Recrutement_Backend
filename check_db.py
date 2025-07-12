#!/usr/bin/env python3
"""
Script simple pour vérifier les données dans la base de données
"""
import psycopg2
import json
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'technova_db'),
    'user': os.getenv('DB_USER', 'technova_user'),
    'password': os.getenv('DB_PASSWORD', 'technova_password')
}

def check_database():
    """Vérifier les données dans la base de données"""
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer tous les candidats
        cursor.execute("""
            SELECT id, name, culture_score, interview_score, 
                   predictive_score, score_details, status
            FROM candidates
        """)
        
        candidates = cursor.fetchall()
        
        print(f"Nombre de candidats trouvés: {len(candidates)}")
        print("="*50)
        
        for candidate in candidates:
            print(f"\n=== Candidat {candidate['name']} (ID: {candidate['id']}) ===")
            print(f"Culture Score: {candidate['culture_score']}")
            print(f"Interview Score: {candidate['interview_score']}")
            print(f"Predictive Score: {candidate['predictive_score']}")
            print(f"Status: {candidate['status']}")
            print(f"Score Details (raw): {candidate['score_details']}")
            
            # Parsing des score_details
            if candidate['score_details']:
                try:
                    if isinstance(candidate['score_details'], str):
                        score_details = json.loads(candidate['score_details'])
                    else:
                        score_details = candidate['score_details']
                    
                    print(f"Score Details (parsed):")
                    for key, value in score_details.items():
                        print(f"  {key}: {value}")
                        
                except Exception as e:
                    print(f"Erreur parsing score_details: {e}")
            
            print("-" * 40)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur lors de la connexion à la base de données: {e}")

if __name__ == "__main__":
    check_database()
