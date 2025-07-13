#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append('.')

def test_gemini_simple():
    """Test ultra simple de l'API Gemini"""
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        # Charger les variables d'environnement
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ Clé API Gemini manquante dans .env")
            return False
        
        print(f"✅ Clé API trouvée: {api_key[:10]}...")
        
        # Configurer l'API
        genai.configure(api_key=api_key)
        
        # Test ultra simple
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Dis juste: OK")
        
        if response and response.text:
            print(f"✅ Réponse API: {response.text.strip()}")
            return True
        else:
            print("❌ Pas de réponse de l'API")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_gemini_json():
    """Test avec un prompt JSON simple"""
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        import json
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """Réponds avec ce JSON exact:
        {"test": "success", "number": 42}"""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            print(f"✅ Réponse brute: {response.text.strip()}")
            
            # Essayer de parser le JSON
            try:
                json_data = json.loads(response.text.strip())
                print(f"✅ JSON parsé: {json_data}")
                return True
            except json.JSONDecodeError:
                print("❌ Réponse non JSON")
                return False
        else:
            print("❌ Pas de réponse")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Test API Gemini ===")
    
    print("\n1. Test simple:")
    simple_ok = test_gemini_simple()
    
    if simple_ok:
        print("\n2. Test JSON:")
        json_ok = test_gemini_json()
    else:
        print("\n❌ Test simple échoué, arrêt des tests")
        json_ok = False
    
    print("\n=== Résultat ===")
    if simple_ok and json_ok:
        print("✅ API Gemini fonctionne correctement")
    else:
        print("❌ Problème avec l'API Gemini")
