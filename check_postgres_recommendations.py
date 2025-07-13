#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
import psycopg2
import json

load_dotenv()

def check_postgres_recommendations():
    """Vérifie les recommandations et risques dans PostgreSQL"""
    
    try:
        # Configuration de la base de données
        database_url = os.getenv('DATABASE_URL')
        print(f"🔗 URL de la base: {database_url[:50]}..." if database_url else "❌ Pas de DATABASE_URL")
        
        if not database_url:
            print("❌ Variable DATABASE_URL non trouvée dans .env")
            return
        
        # Connexion à PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connexion PostgreSQL réussie")
        
        # Vérifier si la table candidate existe
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        tables = cursor.fetchall()
        print(f"📊 Tables trouvées: {[t[0] for t in tables]}")
        
        if ('candidate',) not in tables:
            print("❌ Table 'candidate' non trouvée")
            return
        
        # Vérifier la structure de la table candidate
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'candidate';
        """)
        columns = cursor.fetchall()
        print(f"🏗️ Colonnes de la table candidate:")
        for col_name, col_type in columns:
            print(f"   - {col_name} ({col_type})")
        
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
                ORDER BY id DESC
                LIMIT 5;
            """)
            candidates = cursor.fetchall()
            
            print(f"\n📋 Détails des 5 derniers candidats:")
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
                        for i, risk in enumerate(parsed_risks[:3], 1):  # Afficher max 3
                            if isinstance(risk, dict):
                                risk_text = risk.get('risk', risk.get('description', str(risk)))
                                print(f"      {i}. {risk_text[:100]}...")
                            else:
                                print(f"      {i}. {str(risk)[:100]}...")
                    except json.JSONDecodeError:
                        print(f"   🚨 Risques (brut): {str(risks)[:100]}...")
                    except Exception as e:
                        print(f"   🚨 Erreur parsing risques: {e}")
                else:
                    print(f"   🚨 Risques: VIDES")
                
                # Parser les recommandations
                if recommendations:
                    try:
                        parsed_recs = json.loads(recommendations)
                        print(f"   💡 Recommandations: {len(parsed_recs)} éléments")
                        for i, rec in enumerate(parsed_recs[:3], 1):  # Afficher max 3
                            if isinstance(rec, dict):
                                rec_text = f"{rec.get('type', 'Type')}: {rec.get('description', str(rec))}"
                                print(f"      {i}. {rec_text[:100]}...")
                            else:
                                print(f"      {i}. {str(rec)[:100]}...")
                    except json.JSONDecodeError:
                        print(f"   💡 Recommandations (brut): {str(recommendations)[:100]}...")
                    except Exception as e:
                        print(f"   💡 Erreur parsing recommandations: {e}")
                else:
                    print(f"   💡 Recommandations: VIDES")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'accès à PostgreSQL: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_postgres_recommendations()
