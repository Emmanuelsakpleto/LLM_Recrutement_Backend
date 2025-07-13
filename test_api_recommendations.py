#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_api_recommendations():
    """Test pour vérifier que l'API retourne bien les recommandations et risques"""
    
    # URL de l'API
    base_url = "http://localhost:5000"
    
    # Headers avec token d'authentification (à adapter selon votre système)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MjQxMTYxNCwianRpIjoiOTUyNDFiNWQtOGE4ZS00M2UxLTg3NjctMmJhYzk1NjcxYWY0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NTI0MTE2MTQsImNzcmYiOiJiYjgzMGFjOS03YmU0LTQ1ZWMtYjEzYi04NjVhY2U3NDlhNTIiLCJleHAiOjE3NTI0OTgwMTR9.ZPW1SFDJddMukTSvJpz3VsCjGrql7lRw-rZz0hTB1dc'
    }
    
    print("🔍 Test de l'API - Récupération des candidats...")
    
    try:
        # Appel à l'API candidates
        response = requests.get(f"{base_url}/api/candidates", headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Réponse reçue - Nombre de candidats: {len(data)}")
            
            # Vérifier les candidats un par un
            for i, candidate in enumerate(data):
                print(f"\n👤 Candidat {i+1}: {candidate.get('name', 'N/A')}")
                print(f"   📈 Score final: {candidate.get('final_score', 'N/A')}")
                
                # Vérifier la présence des recommandations et risques
                recommendations = candidate.get('recommendations')
                risks = candidate.get('risks')
                
                print(f"   📋 Recommandations: {'✅ Présentes' if recommendations else '❌ Absentes'}")
                print(f"   ⚠️  Risques: {'✅ Présents' if risks else '❌ Absents'}")
                
                if recommendations:
                    print(f"      📋 Nombre de recommandations: {len(recommendations)}")
                    print(f"      📋 Première recommandation: {recommendations[0]}")
                
                if risks:
                    print(f"      ⚠️  Nombre de risques: {len(risks)}")
                    print(f"      ⚠️  Premier risque: {risks[0]}")
                
                # Afficher les détails des scores
                score_details = candidate.get('score_details', {})
                print(f"   📊 Détails scores: {score_details}")
            
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"   Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_api_recommendations()
