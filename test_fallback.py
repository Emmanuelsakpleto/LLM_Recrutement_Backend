#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
sys.path.append('.')

# Test direct du fallback sans API
def test_fallback_questions():
    """Test direct du système de fallback"""
    from app.modules.llms import generate_fallback_questions
    
    job_desc = {
        'title': 'Développeur Python',
        'skills': ['Python', 'Django', 'API REST'],
        'required_experience_years': 3
    }

    cv_data = {
        'Compétences': ['Python', 'JavaScript', 'SQL'],
        'Formations': [{'diplôme': 'Master Informatique'}]
    }

    score_result = {
        'skills_score': 85,
        'experience_score': 75,
        'education_score': 90
    }

    print("🚀 Test du système de fallback...")
    result = generate_fallback_questions(job_desc, cv_data, score_result)
    
    if "questions" in result:
        print(f"✅ {len(result['questions'])} questions générées")
        print("📋 Exemple de questions:")
        for i, q in enumerate(result['questions'][:3]):
            print(f"  {i+1}. [{q['category']}] {q['question']}")
        return True
    else:
        print(f"❌ Échec: {result}")
        return False

if __name__ == "__main__":
    success = test_fallback_questions()
    if success:
        print("\n✅ Test du fallback réussi !")
    else:
        print("\n❌ Test du fallback échoué !")
