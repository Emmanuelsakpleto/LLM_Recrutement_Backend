#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
sys.path.append('.')

def test_question_generation():
    """Test complet du système de génération de questions"""
    from app.modules.llms import generate_interview_questions
    
    job_desc = {
        'title': 'Développeur Python',
        'skills': ['Python', 'Django', 'API REST', 'PostgreSQL'],
        'required_experience_years': 3
    }

    cv_data = {
        'Compétences': ['Python', 'JavaScript', 'SQL', 'Docker'],
        'Formations': [{'diplôme': 'Master Informatique'}]
    }

    score_result = {
        'skills_score': 85,
        'experience_score': 75,
        'education_score': 90
    }

    print("🚀 Test du système complet de génération...")
    print("📋 Données d'entrée:")
    print(f"   • Poste: {job_desc['title']}")
    print(f"   • Compétences requises: {', '.join(job_desc['skills'])}")
    print(f"   • Compétences candidat: {', '.join(cv_data['Compétences'])}")
    
    result = generate_interview_questions(job_desc, cv_data, score_result)
    
    if "questions" in result:
        questions = result["questions"]
        print(f"\n✅ {len(questions)} questions générées")
        
        # Analyser par catégorie
        categories = {}
        for q in questions:
            cat = q['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(q)
        
        print("\n📊 Répartition par catégorie:")
        for cat, cat_questions in categories.items():
            print(f"   • {cat}: {len(cat_questions)} questions")
        
        print("\n� Exemples de questions:")
        for i, q in enumerate(questions[:5], 1):
            print(f"   {i}. [{q['category']}] {q['question']}")
            print(f"      → {q['purpose']}")
        
        if len(questions) > 5:
            print(f"   ... et {len(questions) - 5} autres questions")
        
        return True
    else:
        print(f"❌ Erreur: {result}")
        return False

if __name__ == "__main__":
    success = test_question_generation()
    if success:
        print("\n🎉 Test réussi ! Le système de génération fonctionne.")
    else:
        print("\n💥 Test échoué.")
