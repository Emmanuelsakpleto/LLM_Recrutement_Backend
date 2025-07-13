#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Générateur de questions d'entretien intelligent basé sur des templates
Alternative professionnelle à l'API Gemini
"""

import json
import random
from typing import Dict, List, Any

class InterviewQuestionGenerator:
    def __init__(self):
        self.templates = {
            "Job_Description": {
                "technical_skills": [
                    "Pouvez-vous expliquer votre expérience avec {skill} et comment vous l'avez utilisée dans vos projets précédents ?",
                    "Quels sont les défis les plus complexes que vous avez rencontrés avec {skill} et comment les avez-vous résolus ?",
                    "Comment évaluez-vous votre niveau de maîtrise de {skill} et quelles sont vos perspectives d'amélioration ?",
                    "Décrivez un projet concret où {skill} a été déterminant pour le succès de la réalisation.",
                    "Quelles sont les meilleures pratiques que vous appliquez quand vous travaillez avec {skill} ?"
                ],
                "experience": [
                    "Avec {years} ans d'expérience requise, comment votre parcours vous a-t-il préparé à ce poste ?",
                    "Décrivez une situation où votre expérience a été cruciale pour résoudre un problème complexe.",
                    "Comment votre expérience vous permet-elle d'aborder les défis de ce poste de {title} ?",
                    "Quels apprentissages de votre expérience passée souhaitez-vous appliquer dans ce rôle ?"
                ],
                "general": [
                    "Qu'est-ce qui vous motive le plus dans un poste de {title} ?",
                    "Comment voyez-vous l'évolution de votre carrière dans ce domaine ?",
                    "Quels sont vos objectifs professionnels à court et moyen terme ?",
                    "Comment définiriez-vous un environnement de travail idéal pour vous ?"
                ]
            },
            "Company_Culture": {
                "innovation": [
                    "Comment abordez-vous l'innovation dans votre travail quotidien ?",
                    "Décrivez une situation où vous avez proposé une solution innovante.",
                    "Que signifie l'innovation pour vous dans un contexte professionnel ?",
                    "Comment restez-vous à jour avec les dernières tendances de votre domaine ?"
                ],
                "collaboration": [
                    "Décrivez votre approche du travail en équipe.",
                    "Comment gérez-vous les conflits ou désaccords au sein d'une équipe ?",
                    "Donnez un exemple de collaboration réussie que vous avez menée.",
                    "Quel rôle préférez-vous jouer dans une équipe projet ?"
                ],
                "transparency": [
                    "Comment communiquez-vous sur vos difficultés ou erreurs ?",
                    "Quelle est votre approche pour donner et recevoir du feedback ?",
                    "Comment assurez-vous la transparence dans vos projets ?",
                    "Décrivez une situation où la transparence a été clé dans votre travail."
                ],
                "client_impact": [
                    "Comment mesurez-vous l'impact de votre travail sur les clients ?",
                    "Décrivez une situation où vous avez amélioré l'expérience client.",
                    "Quelle est votre approche pour comprendre les besoins clients ?",
                    "Comment intégrez-vous la perspective client dans vos décisions ?"
                ]
            },
            "CV_Professional_Life": {
                "skills_validation": [
                    "Votre CV mentionne {skill}. Pouvez-vous détailler votre expérience pratique avec cette technologie ?",
                    "Parmi vos compétences ({skills}), laquelle considérez-vous comme votre point fort ?",
                    "Comment avez-vous développé votre expertise en {skill} ?",
                    "Quels projets vous ont permis d'approfondir vos compétences en {skills} ?"
                ],
                "education": [
                    "Comment votre formation en {education} vous a-t-elle préparé à ce poste ?",
                    "Quels aspects de votre formation appliquez-vous encore aujourd'hui ?",
                    "Y a-t-il des domaines de votre formation que vous souhaitez approfondir ?",
                    "Comment complétez-vous votre formation initiale par l'apprentissage continu ?"
                ],
                "experience_analysis": [
                    "Quel a été votre projet le plus marquant et pourquoi ?",
                    "Comment avez-vous évolué professionnellement ces dernières années ?",
                    "Quels défis avez-vous rencontrés dans votre parcours et comment les avez-vous surmontés ?",
                    "Qu'est-ce qui vous a motivé à postuler pour ce poste maintenant ?"
                ],
                "career_progression": [
                    "Comment envisagez-vous la suite de votre carrière ?",
                    "Quelles compétences souhaitez-vous développer dans ce poste ?",
                    "Qu'est-ce qui vous motive dans votre évolution professionnelle ?",
                    "Comment ce poste s'inscrit-il dans votre projet de carrière ?"
                ]
            }
        }
    
    def generate_questions(self, job_description: Dict, cv_data: Dict, score_result: Dict) -> Dict:
        """Génère 15 questions intelligentes basées sur le profil"""
        all_questions = []
        
        # Questions Job Description (5)
        job_questions = self._generate_job_questions(job_description)
        all_questions.extend(job_questions)
        
        # Questions Company Culture (5)
        culture_questions = self._generate_culture_questions()
        all_questions.extend(culture_questions)
        
        # Questions CV/Professional Life (5)
        cv_questions = self._generate_cv_questions(cv_data, score_result)
        all_questions.extend(cv_questions)
        
        return {"questions": all_questions}
    
    def _generate_job_questions(self, job_description: Dict) -> List[Dict]:
        """Génère les questions liées au poste"""
        questions = []
        templates = self.templates["Job_Description"]
        
        title = job_description.get("title", "ce poste")
        skills = job_description.get("skills", [])
        years = job_description.get("required_experience_years", 3)
        
        # 2 questions techniques sur les compétences
        if skills:
            selected_skills = random.sample(skills, min(2, len(skills)))
            for skill in selected_skills:
                template = random.choice(templates["technical_skills"])
                questions.append({
                    "category": "Job Description",
                    "question": template.format(skill=skill),
                    "purpose": f"Évaluer la maîtrise de {skill}"
                })
        
        # 1 question sur l'expérience
        exp_template = random.choice(templates["experience"])
        questions.append({
            "category": "Job Description",
            "question": exp_template.format(years=years, title=title),
            "purpose": "Évaluer l'expérience pertinente"
        })
        
        # 2 questions générales
        for _ in range(2):
            gen_template = random.choice(templates["general"])
            questions.append({
                "category": "Job Description",
                "question": gen_template.format(title=title),
                "purpose": "Évaluer la motivation et la vision"
            })
        
        return questions
    
    def _generate_culture_questions(self) -> List[Dict]:
        """Génère les questions sur la culture d'entreprise"""
        questions = []
        templates = self.templates["Company_Culture"]
        
        # Une question de chaque catégorie culturelle
        categories = ["innovation", "collaboration", "transparency", "client_impact"]
        
        for category in categories:
            template = random.choice(templates[category])
            questions.append({
                "category": "Company Culture",
                "question": template,
                "purpose": f"Évaluer l'adéquation avec la valeur {category}"
            })
        
        # Une question supplémentaire aléatoire
        random_category = random.choice(categories)
        template = random.choice(templates[random_category])
        questions.append({
            "category": "Company Culture",
            "question": template,
            "purpose": f"Approfondir l'évaluation de {random_category}"
        })
        
        return questions
    
    def _generate_cv_questions(self, cv_data: Dict, score_result: Dict) -> List[Dict]:
        """Génère les questions basées sur le CV"""
        questions = []
        templates = self.templates["CV_Professional_Life"]
        
        skills = cv_data.get("Compétences", [])
        education = cv_data.get("Formations", [{}])[0].get("diplôme", "votre formation")
        
        # 2 questions sur les compétences
        if skills:
            selected_skills = random.sample(skills, min(2, len(skills)))
            for skill in selected_skills:
                template = random.choice(templates["skills_validation"])
                questions.append({
                    "category": "CV/Professional Life",
                    "question": template.format(skill=skill, skills=", ".join(skills)),
                    "purpose": f"Valider la compétence {skill}"
                })
        
        # 1 question sur la formation
        edu_template = random.choice(templates["education"])
        questions.append({
            "category": "CV/Professional Life",
            "question": edu_template.format(education=education),
            "purpose": "Évaluer l'apport de la formation"
        })
        
        # 2 questions sur l'expérience et la carrière
        exp_template = random.choice(templates["experience_analysis"])
        questions.append({
            "category": "CV/Professional Life",
            "question": exp_template,
            "purpose": "Analyser l'expérience professionnelle"
        })
        
        career_template = random.choice(templates["career_progression"])
        questions.append({
            "category": "CV/Professional Life",
            "question": career_template,
            "purpose": "Évaluer la progression de carrière"
        })
        
        return questions

# Fonction d'interface pour remplacer l'API Gemini
def generate_intelligent_questions(job_description: Dict, cv_data: Dict, score_result: Dict) -> Dict:
    """Génère des questions intelligentes sans API externe"""
    generator = InterviewQuestionGenerator()
    return generator.generate_questions(job_description, cv_data, score_result)

if __name__ == "__main__":
    # Test du générateur
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

    print("🚀 Test du générateur intelligent...")
    result = generate_intelligent_questions(job_desc, cv_data, score_result)
    
    if "questions" in result:
        print(f"✅ {len(result['questions'])} questions générées")
        
        # Afficher par catégorie
        categories = {}
        for q in result['questions']:
            cat = q['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(q)
        
        for cat, questions in categories.items():
            print(f"\n📂 {cat} ({len(questions)} questions):")
            for i, q in enumerate(questions, 1):
                print(f"   {i}. {q['question']}")
                print(f"      → {q['purpose']}")
    else:
        print(f"❌ Erreur: {result}")
