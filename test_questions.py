#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append('.')
from app.modules.llms import generate_questions_for_category, generate_interview_questions
import json

def test_single_category():
    """Test direct d'une catégorie"""
    prompt = """
    Créez exactement 5 questions d'entretien RH pour évaluer un candidat au poste de Développeur Python.
    Compétences requises: Python, Django, API REST
    Expérience requise: 3 ans
    
    Retournez UNIQUEMENT un JSON avec cette structure exacte:
    {
        "questions": [
            {"category": "Job Description", "question": "Question technique 1?", "purpose": "Évaluer compétence X"},
            {"category": "Job Description", "question": "Question technique 2?", "purpose": "Évaluer compétence Y"},
            {"category": "Job Description", "question": "Question technique 3?", "purpose": "Évaluer compétence Z"},
            {"category": "Job Description", "question": "Question technique 4?", "purpose": "Évaluer expérience"},
            {"category": "Job Description", "question": "Question technique 5?", "purpose": "Évaluer approche"}
        ]
    }
    """
    
    print("🚀 Test direct de génération...")
    result = generate_questions_for_category(prompt, 'Job_Description')
    print(f"✅ Résultat: {result}")
    return result

def test_full_generation():
    """Test de la génération complète"""
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

    print("🚀 Test de génération complète...")
    result = generate_interview_questions(job_desc, cv_data, score_result)
    print(f"✅ Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

if __name__ == "__main__":
    print("=== Test de génération de questions ===")
    
    # Test 1 : Une seule catégorie
    print("\n1. Test catégorie unique:")
    single_result = test_single_category()
    
    # Test 2 : Génération complète
    print("\n2. Test génération complète:")
    full_result = test_full_generation()
    
    print("\n=== Fin des tests ===")
