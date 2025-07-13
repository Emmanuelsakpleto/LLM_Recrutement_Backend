#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini_api():
    """Test direct de l'API Gemini"""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Clé API manquante")
        return False
    
    print(f"✅ Clé API trouvée: {api_key[:10]}...")
    
    try:
        # Configuration de l'API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test simple
        print("🚀 Test de l'API Gemini...")
        response = model.generate_content("Réponds simplement: 'API fonctionnelle'")
        
        if response and response.text:
            print(f"✅ Réponse API: {response.text}")
            return True
        else:
            print("❌ Aucune réponse de l'API")
            return False
            
    except Exception as e:
        print(f"❌ Erreur API: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_api()
