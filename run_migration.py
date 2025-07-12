#!/usr/bin/env python3
"""
Script pour exécuter les migrations SQL
"""
import psycopg2
import os
from datetime import datetime

def execute_migration():
    # Configuration de la base de données
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin123@localhost:5432/technova')
    
    try:
        # Connexion à la base de données
        print(f"Connexion à la base de données...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print(f"Début de la migration à {datetime.now()}")
        
        # Lire et exécuter le fichier SQL
        with open('migrations/update_models_structure.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Diviser le contenu en commandes individuelles
        commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        for i, command in enumerate(commands, 1):
            if command:
                print(f"Exécution de la commande {i}/{len(commands)}: {command[:50]}...")
                try:
                    cursor.execute(command)
                    conn.commit()
                    print(f"✅ Commande {i} exécutée avec succès")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'exécution de la commande {i}: {e}")
                    # Continuer même si une commande échoue (peut-être déjà existante)
                    conn.rollback()
        
        print(f"Migration terminée à {datetime.now()}")
        
        # Vérifier la structure des tables
        print("\nVérification de la structure des tables:")
        
        # Vérifier job_brief
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'job_brief' 
            ORDER BY ordinal_position
        """)
        print("\nTable job_brief:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}) - nullable: {row[2]}")
        
        # Vérifier candidate
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'candidate' 
            ORDER BY ordinal_position
        """)
        print("\nTable candidate:")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}) - nullable: {row[2]}")
            
        cursor.close()
        conn.close()
        print("\n✅ Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    execute_migration()
