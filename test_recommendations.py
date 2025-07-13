#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.modules.llms import generate_predictive_analysis
import json

def test_recommendations_generation():
    """Test si les recommandations et risques sont bien générés"""
    
    # Données de test simulées
    job_description = {
        "title": "Développeur Python",
        "skills": ["Python", "Django", "PostgreSQL"],
        "required_experience_years": 3
    }
    
    cv_data = {
        "Compétences": ["Python", "HTML", "CSS"],
        "Formations": [{"diplôme": "Master en Informatique", "institution": "Université"}],
        "Expériences professionnelles": [
            {"poste": "Développeur Junior", "durée": "2 ans", "description": "Développement web"}
        ]
    }
    
    score_result = {
        "skills_score": 75.0,
        "experience_score": 60.0,
        "education_score": 85.0,
        "culture_score": 70.0,
        "interview_score": 80.0,
        "final_score": 72.0
    }
    
    questions_data = {
        "questions": [
            {"category": "Job Description", "question": "Test question 1?", "purpose": "Test"},
            {"category": "Company Culture", "question": "Test question 2?", "purpose": "Test"},
            {"category": "CV/Professional Life", "question": "Test question 3?", "purpose": "Test"}
        ]
    }
    
    # Données d'appréciations simulées
    appreciations_data = [
        {"question": "Test question 1?", "category": "Job Description", "appreciation": "satisfait", "score": 75},
        {"question": "Test question 2?", "category": "Company Culture", "appreciation": "très satisfait", "score": 100},
        {"question": "Test question 3?", "category": "CV/Professional Life", "appreciation": "satisfait", "score": 75}
    ]
    
    print("🧪 Test de génération des recommandations et risques...")
    
    try:
        # Appeler la fonction de génération
        result = generate_predictive_analysis(
            job_description, 
            cv_data, 
            score_result, 
            questions_data, 
            appreciations_data
        )
        
        print(f"📊 Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "error" in result:
            print(f"❌ Erreur détectée: {result['error']}")
        else:
            print("✅ Génération réussie!")
            
            # Vérifier la présence des clés importantes
            if "risks" in result and "recommendations" in result:
                print(f"🎯 Risques générés: {len(result['risks'])} éléments")
                print(f"📋 Recommandations générées: {len(result['recommendations'])} éléments")
                
                # Afficher les détails
                print("\n🚨 RISQUES:")
                for i, risk in enumerate(result['risks'], 1):
                    print(f"   {i}. {risk}")
                
                print("\n💡 RECOMMANDATIONS:")
                for i, rec in enumerate(result['recommendations'], 1):
                    print(f"   {i}. {rec}")
            else:
                print("❌ Clés manquantes dans le résultat")
                
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recommendations_generation()
