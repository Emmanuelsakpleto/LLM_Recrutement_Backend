# -*- coding: utf-8 -*-
import os
import time
import random
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import google.generativeai as genai
import logging
import torch
import re
import json
from sentence_transformers import SentenceTransformer
import gc

# Configuration des logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("La clé API Gemini n'est pas définie dans le fichier .env")

# Variable globale pour le modèle Sentence Transformer
_model_instance = None

def get_sentence_transformer():
    global _model_instance
    if _model_instance is None:
        # Libérer la mémoire cache CUDA si possible
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Forcer le garbage collector
        gc.collect()
        
        # Charger le modèle avec des options d'optimisation mémoire
        _model_instance = SentenceTransformer(
            'distiluse-base-multilingual-cased-v1',  # Modèle plus léger
            device='cpu'  # Forcer l'utilisation du CPU
        )
    return _model_instance

# Générateur intelligent de questions (fallback professionnel)
def generate_intelligent_questions(job_description, cv_data, score_result):
    """Générateur de questions intelligent basé sur des templates"""
    templates = {
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
    
    all_questions = []
    
    # Extraction des données
    title = job_description.get("title", "ce poste")
    skills = job_description.get("skills", [])
    years = job_description.get("required_experience_years", 3)
    cv_skills = cv_data.get("Compétences", [])
    education = cv_data.get("Formations", [{}])[0].get("diplôme", "votre formation")
    
    # Questions Job Description (5)
    job_templates = templates["Job_Description"]
    
    # 2 questions techniques sur les compétences
    if skills:
        selected_skills = random.sample(skills, min(2, len(skills)))
        for skill in selected_skills:
            template = random.choice(job_templates["technical_skills"])
            all_questions.append({
                "category": "Job Description",
                "question": template.format(skill=skill),
                "purpose": f"Évaluer la maîtrise de {skill}"
            })
    
    # 1 question sur l'expérience
    exp_template = random.choice(job_templates["experience"])
    all_questions.append({
        "category": "Job Description",
        "question": exp_template.format(years=years, title=title),
        "purpose": "Évaluer l'expérience pertinente"
    })
    
    # 2 questions générales
    for _ in range(5 - len(all_questions)):
        gen_template = random.choice(job_templates["general"])
        all_questions.append({
            "category": "Job Description",
            "question": gen_template.format(title=title),
            "purpose": "Évaluer la motivation et la vision"
        })
    
    # Questions Company Culture (5)
    culture_templates = templates["Company_Culture"]
    categories = ["innovation", "collaboration", "transparency", "client_impact"]
    
    for category in categories:
        template = random.choice(culture_templates[category])
        all_questions.append({
            "category": "Company Culture",
            "question": template,
            "purpose": f"Évaluer l'adéquation avec la valeur {category}"
        })
    
    # Une question supplémentaire aléatoire
    random_category = random.choice(categories)
    template = random.choice(culture_templates[random_category])
    all_questions.append({
        "category": "Company Culture",
        "question": template,
        "purpose": f"Approfondir l'évaluation de {random_category}"
    })
    
    # Questions CV/Professional Life (5)
    cv_templates = templates["CV_Professional_Life"]
    
    # 2 questions sur les compétences CV
    if cv_skills:
        selected_skills = random.sample(cv_skills, min(2, len(cv_skills)))
        for skill in selected_skills:
            template = random.choice(cv_templates["skills_validation"])
            all_questions.append({
                "category": "CV/Professional Life",
                "question": template.format(skill=skill, skills=", ".join(cv_skills)),
                "purpose": f"Valider la compétence {skill}"
            })
    
    # 1 question sur la formation
    edu_template = random.choice(cv_templates["education"])
    all_questions.append({
        "category": "CV/Professional Life",
        "question": edu_template.format(education=education),
        "purpose": "Évaluer l'apport de la formation"
    })
    
    # 2 questions sur l'expérience et la carrière
    for _ in range(5 - (len(all_questions) - 10)):  # Compléter pour avoir 5 questions CV
        if len(all_questions) % 2 == 0:
            template = random.choice(cv_templates["experience_analysis"])
            purpose = "Analyser l'expérience professionnelle"
        else:
            template = random.choice(cv_templates["career_progression"])
            purpose = "Évaluer la progression de carrière"
        
        all_questions.append({
            "category": "CV/Professional Life",
            "question": template,
            "purpose": purpose
        })
    
    logger.info(f"✅ Générateur intelligent: {len(all_questions)} questions créées")
    return {"questions": all_questions}

try:
    # Configuration de l'API Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("API Gemini configurée avec succès")
except Exception as e:
    logger.error(f"Erreur lors de la configuration de l'API Gemini: {str(e)}")
    raise

def generate_job_description(data):
    try:
        logger.info("🚀 Début de la génération de description")
        logger.info(f"📝 Données reçues: {data}")
        
        if not GEMINI_API_KEY:
            logger.error("❌ Clé API Gemini manquante")
            raise ValueError("Configuration API manquante")

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ API Gemini configurée")

        prompt = f"""
        Créez une description de poste professionnelle pour :
        - Poste : {data['title']}
        - Compétences : {data['skills']}
        - Expérience : {data['experience']} ans
        - Contexte : {data['description']}
        """
        
        logger.info("📤 Envoi de la requête à Gemini")
        response = model.generate_content(prompt)
        
        if response and response.text:
            logger.info("✅ Description générée avec succès")
            return response.text
        else:
            logger.error("❌ Aucune réponse de l'API")
            raise ValueError("Génération échouée")
            
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}")
        raise

# Fonctions utilitaires
def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    return torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0), dim=1).item()

# Désactiver les avertissements de symlinks pour Hugging Face
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "true"

# Charger la clé API depuis .env
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Clé API Gemini manquante. Vérifiez le fichier .env.")

# Configurer Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Utiliser la fonction get_sentence_transformer au lieu d'une instance globale
def get_embeddings(text):
    model = get_sentence_transformer()
    return model.encode(text)

print("Configuration initiale terminée avec succès !")

def generate_job_description(brief, model="gemini-1.5-flash"):
    try:
        gen_model = genai.GenerativeModel(model)
        prompt = f"""
        Générez une fiche de poste structurée au format JSON à partir du brief suivant : "{brief}". La fiche doit contenir :
        - "title" : Titre du poste
        - "description" : Description générale (100-150 mots, ton professionnel)
        - "skills" : Liste des compétences requises
        - "responsibilities" : Liste des responsabilités principales
        - "qualifications" : Liste des qualifications (expérience, formation, etc.)
        - "required_experience_years" : Nombre d'années d'expérience requises (nombre)
        - "required_degree" : Diplôme requis (ex. "Bachelor", "Master")
        Retournez EXCLUSIVEMENT un seul objet JSON valide, sans texte explicatif, sans balises ```json, sans répétition.
        """
        response = gen_model.generate_content(prompt)
        text = response.text.strip()
        json_match = re.search(r'\{[\s\S]*?\}(?=\s*\{|$)', text)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            print("Erreur : Aucun JSON valide trouvé dans la réponse")
            return None
    except Exception as e:
        print(f"Erreur lors de la génération de la fiche de poste : {str(e)}")
        return None

def extract_text_from_pdf(pdf_path):
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    except Exception as e:
        return f"Erreur lors de l'extraction du PDF : {str(e)}"

def analyze_cv(cv_text, model="gemini-1.5-flash"):
    try:
        gen_model = genai.GenerativeModel(model)
        prompt = f"""
        Analyse le CV suivant et extrais les informations clés sous forme de JSON structuré :
        - Compétences : liste de chaînes (ex. ["Python", "Java"])
        - Expériences professionnelles : liste d'objets avec poste, entreprise, durée, description
        - Formations : liste d'objets avec diplôme, institution, année
        CV : {cv_text}
        Retourne UNIQUEMENT un JSON valide, sans texte supplémentaire, sans balises markdown.
        """
        response = gen_model.generate_content(prompt)
        cleaned_response = re.sub(r'^```json\n|```$', '', response.text, flags=re.MULTILINE).strip()
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        return {"error": f"Impossible de parser la réponse en JSON : {str(e)}", "raw_response": response.text}
    except Exception as e:
        return {"error": f"Erreur lors de l'analyse avec Gemini : {str(e)}"}

def calculate_cv_score(cv_data, job_description):
    try:
        logger.info(f"🎯 Calcul du score CV - CV data: {cv_data}")
        logger.info(f"🎯 Calcul du score CV - Job desc: {job_description}")
        
        skills_score = 0.0
        experience_score = 0.0
        education_score = 0.0       
        cv_skills = cv_data.get("Compétences", [])
        job_skills = job_description.get("skills", [])
        
        logger.info(f"🔧 CV skills: {cv_skills}")
        logger.info(f"🔧 Job skills: {job_skills}")
        
        if cv_skills and job_skills:
            # Utiliser get_embeddings avec conversion en tenseur PyTorch
            cv_embeddings = torch.tensor(get_embeddings(cv_skills))
            job_embeddings = torch.tensor(get_embeddings(job_skills))
            
            logger.info(f"📊 CV embeddings shape: {cv_embeddings.shape}")
            logger.info(f"📊 Job embeddings shape: {job_embeddings.shape}")
            
            # Calculer les similarités individuelles
            similarities = []
            for cv_emb in cv_embeddings:
                skill_similarities = []
                for job_emb in job_embeddings:
                    similarity = cosine_similarity(cv_emb, job_emb)
                    skill_similarities.append(similarity)
                similarities.append(max(skill_similarities))
            
            # Calculer le score moyen
            skills_score = sum(similarities) / len(similarities) if similarities else 0.0
            logger.info(f"🎯 Skills score calculé: {skills_score}")

        cv_experiences = cv_data.get("Expériences professionnelles", [])
        required_years = job_description.get("required_experience_years", 0)
        logger.info(f"💼 CV experiences: {cv_experiences}")
        logger.info(f"💼 Required years: {required_years}")
        
        if cv_experiences:
            total_years = 0
            for exp in cv_experiences:
                duration = exp.get("durée", "").lower()
                if "ans" in duration or "an" in duration:
                    match = re.search(r'(\d+\.?\d*)', duration)
                    if match:
                        total_years += float(match.group(1))
                elif "mois" in duration:
                    match = re.search(r'(\d+\.?\d*)', duration)
                    if match:
                        total_years += float(match.group(1)) / 12
                elif "-" in duration:
                    months = 2
                    total_years += months / 12
            
            # Gestion spéciale pour les postes de stagiaire (0 ans requis)
            if required_years == 0:
                # Pour un poste de stagiaire, toute expérience est un bonus
                # Score basé sur l'expérience existante (plafonné à 100%)
                experience_score = min(total_years * 0.5, 1.0)  # 2 ans d'expérience = score maximum
                logger.info(f"💼 Poste de stagiaire détecté - Bonus d'expérience appliqué")
            else:
                # Calcul normal pour les postes avec expérience requise
                experience_score = min(total_years / required_years, 1.0)
            
            logger.info(f"💼 Total years calculated: {total_years}")
            logger.info(f"💼 Experience score: {experience_score}")
        else:
            # Aucune expérience dans le CV
            if required_years == 0:
                # Pour un poste de stagiaire sans expérience requise, c'est acceptable
                experience_score = 0.8  # Score de base pour un stagiaire sans expérience
                logger.info(f"💼 Poste de stagiaire sans expérience - Score de base appliqué")
            else:
                experience_score = 0.0
                logger.info(f"💼 Aucune expérience trouvée")

        cv_educations = cv_data.get("Formations", [])
        required_degree = job_description.get("required_degree", "")
        logger.info(f"🎓 CV educations: {cv_educations}")
        logger.info(f"🎓 Required degree: {required_degree}")
        
        if cv_educations and required_degree:
            degree_levels = {"Bac": 1, "Licence": 2, "Bachelor": 2, "Master": 3, "Doctorat": 4}
            max_cv_degree_level = 0
            for edu in cv_educations:
                degree = edu.get("diplôme", "")
                for deg, level in degree_levels.items():
                    if deg.lower() in degree.lower():
                        max_cv_degree_level = max(max_cv_degree_level, level)
            required_level = degree_levels.get(required_degree, 1)
            education_score = min(max_cv_degree_level / required_level, 1.0) if required_level > 0 else 0.0
            logger.info(f"🎓 Max degree level: {max_cv_degree_level}")
            logger.info(f"🎓 Required level: {required_level}")
            logger.info(f"🎓 Education score: {education_score}")

        final_score = (0.5 * skills_score + 0.3 * experience_score + 0.2 * education_score) * 100
        
        logger.info(f"🏆 Final score components:")
        logger.info(f"   - Skills: {skills_score * 100}%")
        logger.info(f"   - Experience: {experience_score * 100}%") 
        logger.info(f"   - Education: {education_score * 100}%")
        logger.info(f"   - Final: {final_score}%")

        result = {
            "skills_score": skills_score * 100,
            "experience_score": experience_score * 100,
            "education_score": education_score * 100,
            "final_score": final_score
        }
        
        logger.info(f"🎯 Returning score result: {result}")
        return result
    except Exception as e:
        return {"error": f"Erreur lors du calcul du score : {str(e)}"}

def visualize_scores(score_result):
    if "error" in score_result:
        print("Visualisation impossible : scores non calculés.")
        return

    labels = ["Compétences", "Expérience", "Formation", "Final"]
    scores = [
        score_result["skills_score"],
        score_result["experience_score"],
        score_result["education_score"],
        score_result["final_score"]
    ]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, scores, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.ylim(0, 100)
    plt.title("Évaluation du CV par rapport à la fiche de poste", fontsize=14)
    plt.ylabel("Score (%)", fontsize=12)
    for i, score in enumerate(scores):
        plt.text(i, score + 2, f"{score:.1f}%", ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig("cv_scores.png")  # Sauvegarde pour le frontend
    plt.close()

def generate_final_report(cv_text, cv_data, score_result, job_description):
    try:
        skills_count = len(cv_data.get("Compétences", []))
        exp_count = len(cv_data.get("Expériences professionnelles", []))
        edu_count = len(cv_data.get("Formations", []))
        summary = (
            f"### Résumé de l'Évaluation du CV\n\n"
            f"- **Poste visé** : {job_description.get('title', 'Non spécifié')}\n"
            f"- **Compétences** : {skills_count} compétences identifiées ({', '.join(cv_data.get('Compétences', [])[:3]) + '...' if skills_count > 3 else ', '.join(cv_data.get('Compétences', []))}). Score : {score_result.get('skills_score', 0):.1f}%\n"
            f"- **Expériences** : {exp_count} expériences, principalement dans {cv_data.get('Expériences professionnelles', [{}])[0].get('description', 'divers domaines')[:50]}... Score : {score_result.get('experience_score', 0):.1f}%\n"
            f"- **Formations** : {edu_count} formations, incluant {cv_data.get('Formations', [{}])[0].get('diplôme', 'aucun diplôme')} ({cv_data.get('Formations', [{}])[0].get('institution', '')}). Score : {score_result.get('education_score', 0):.1f}%\n"
            f"- **Score final** : {score_result.get('final_score', 0):.1f}%\n\n"
            f"**Conclusion** : Le candidat présente {'une excellente' if score_result.get('final_score', 0) > 80 else 'une bonne' if score_result.get('final_score', 0) > 60 else 'une certaine'} adéquation avec le poste, avec des compétences techniques solides et une formation pertinente. {'Continuer l’évaluation pour un entretien.' if score_result.get('final_score', 0) > 60 else 'Considérer pour des postes similaires avec moins d’expérience.'}"
        )

        final_output = {
            "cv_text": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text,
            "extracted_cv_data": cv_data,
            "job_description": job_description,
            "scores": score_result,
            "summary": summary
        }

        with open("recruitment_report.json", "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        return final_output
    except Exception as e:
        return {"error": f"Erreur lors de la génération du rapport : {str(e)}"}

def generate_questions_for_category(prompt, category, model="gemini-1.5-flash", max_attempts=3):
    gen_model = genai.GenerativeModel(model)
    for attempt in range(max_attempts):
        try:
            logger.info(f"🎯 Génération questions pour {category} (tentative {attempt + 1})")
            response = gen_model.generate_content(prompt)
            raw_response = response.text.strip()
            
            # Sauvegarder la réponse pour debug
            with open(f"debug_response_{category}.txt", "w", encoding="utf-8") as f:
                f.write(raw_response)
            
            logger.info(f"📝 Réponse brute pour {category}: {raw_response[:200]}...")

            # Nettoyer la réponse en supprimant les balises markdown
            cleaned_response = re.sub(r'^```json\n|```$', '', raw_response, flags=re.MULTILINE).strip()
            
            # Chercher le JSON
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if not json_match:
                logger.warning(f"⚠️ Tentative {attempt + 1} ({category}): Aucun JSON valide trouvé")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                logger.error(f"❌ Échec final pour {category}: Aucun JSON valide")
                return None

            # Parser le JSON
            questions_data = json.loads(json_match.group(0))
            questions = questions_data.get("questions", [])
            
            logger.info(f"📊 {len(questions)} questions trouvées pour {category}")
            
            if len(questions) != 5:
                logger.warning(f"⚠️ Tentative {attempt + 1} ({category}): {len(questions)} questions au lieu de 5")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                logger.error(f"❌ Échec final pour {category}: Nombre incorrect de questions")
                return None

            logger.info(f"✅ Questions générées avec succès pour {category}")
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Tentative {attempt + 1} ({category}): Erreur JSON : {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            logger.error(f"❌ Échec final pour {category}: Erreur JSON")
            return None
        except Exception as e:
            logger.error(f"❌ Tentative {attempt + 1} ({category}): Erreur générale : {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            logger.error(f"❌ Échec final pour {category}: Erreur générale")
            return None
    
    logger.error(f"❌ Échec complet pour {category} après {max_attempts} tentatives")
    return None

def generate_interview_questions(job_description, cv_data, score_result, model="gemini-1.5-flash"):
    try:
        if not job_description or "error" in cv_data or "error" in score_result:
            return {"error": "Données manquantes ou invalides."}

        job_title = job_description.get("title", "Développeur Python")
        job_skills = ", ".join(job_description.get("skills", []))
        required_years = job_description.get("required_experience_years", 3)
        cv_skills = ", ".join(cv_data.get("Compétences", []))
        cv_education = cv_data.get("Formations", [{}])[0].get("diplôme", "Non spécifié")
        experience_score = score_result.get("experience_score", 0)

        company_context = "TechNova est une startup SaaS axée sur l’innovation, la collaboration, la transparence et l’impact client."

        prompts = {
            "Job_Description": f"""
            Créez exactement 5 questions d'entretien RH pour évaluer un candidat au poste de {job_title}.
            Compétences requises: {job_skills}
            Expérience requise: {required_years} ans
            
            Retournez UNIQUEMENT un JSON avec cette structure exacte:
            {{
                "questions": [
                    {{"category": "Job Description", "question": "Question technique 1?", "purpose": "Évaluer compétence X"}},
                    {{"category": "Job Description", "question": "Question technique 2?", "purpose": "Évaluer compétence Y"}},
                    {{"category": "Job Description", "question": "Question technique 3?", "purpose": "Évaluer compétence Z"}},
                    {{"category": "Job Description", "question": "Question technique 4?", "purpose": "Évaluer expérience"}},
                    {{"category": "Job Description", "question": "Question technique 5?", "purpose": "Évaluer approche"}}
                ]
            }}
            """,
            "Company_Culture": f"""
            Créez exactement 5 questions d'entretien RH pour évaluer l'adéquation culturelle d'un candidat.
            Contexte entreprise: {company_context}
            
            Retournez UNIQUEMENT un JSON avec cette structure exacte:
            {{
                "questions": [
                    {{"category": "Company Culture", "question": "Question culture 1?", "purpose": "Évaluer valeur innovation"}},
                    {{"category": "Company Culture", "question": "Question culture 2?", "purpose": "Évaluer collaboration"}},
                    {{"category": "Company Culture", "question": "Question culture 3?", "purpose": "Évaluer transparence"}},
                    {{"category": "Company Culture", "question": "Question culture 4?", "purpose": "Évaluer impact client"}},
                    {{"category": "Company Culture", "question": "Question culture 5?", "purpose": "Évaluer adaptation"}}
                ]
            }}
            """,
            "CV_Professional_Life": f"""
            Créez exactement 5 questions d'entretien RH basées sur le profil du candidat.
            Compétences candidat: {cv_skills}
            Formation: {cv_education}
            Score d'expérience: {experience_score:.1f}%
            
            Retournez UNIQUEMENT un JSON avec cette structure exacte:
            {{
                "questions": [
                    {{"category": "CV/Professional Life", "question": "Question expérience 1?", "purpose": "Approfondir expérience"}},
                    {{"category": "CV/Professional Life", "question": "Question expérience 2?", "purpose": "Valider compétences"}},
                    {{"category": "CV/Professional Life", "question": "Question expérience 3?", "purpose": "Comprendre projets"}},
                    {{"category": "CV/Professional Life", "question": "Question expérience 4?", "purpose": "Évaluer formation"}},
                    {{"category": "CV/Professional Life", "question": "Question expérience 5?", "purpose": "Mesurer ambition"}}
                ]
            }}
            """
        }

        all_questions = []
        
        # Tentative de génération avec l'API Gemini
        try:
            logger.info("🚀 Tentative de génération avec l'API Gemini")
            for category in prompts:
                questions = generate_questions_for_category(prompts[category], category.replace("/", "_"), model)
                if questions is None:
                    logger.warning(f"⚠️ Échec API pour {category}, utilisation du générateur intelligent")
                    # En cas d'échec d'une catégorie, utiliser le générateur intelligent
                    intelligent_result = generate_intelligent_questions(job_description, cv_data, score_result)
                    logger.info("✅ Questions intelligentes générées avec succès")
                    return intelligent_result
                all_questions.extend(questions)

            if len(all_questions) != 15:
                logger.warning(f"⚠️ Nombre incorrect de questions ({len(all_questions)}), utilisation du générateur intelligent")
                intelligent_result = generate_intelligent_questions(job_description, cv_data, score_result)
                logger.info("✅ Questions intelligentes générées avec succès")
                return intelligent_result
                
            logger.info("✅ Questions API générées avec succès")
            
        except Exception as api_error:
            logger.error(f"❌ Erreur API Gemini: {str(api_error)}")
            logger.info("🔄 Basculement vers le générateur intelligent")
            intelligent_result = generate_intelligent_questions(job_description, cv_data, score_result)
            logger.info("✅ Questions intelligentes générées avec succès")
            return intelligent_result

        questions_data = {"questions": all_questions}

        with open("interview_questions.json", "w", encoding="utf-8") as f:
            json.dump(questions_data, f, indent=2, ensure_ascii=False)

        return questions_data
    except Exception as e:
        logger.error(f"❌ Erreur générale dans generate_interview_questions: {str(e)}")
        # Dernier recours : générateur intelligent même en cas d'erreur générale
        try:
            intelligent_result = generate_intelligent_questions(job_description, cv_data, score_result)
            logger.info("✅ Questions intelligentes générées en dernier recours")
            return intelligent_result
        except Exception as fallback_error:
            logger.error(f"❌ Échec complet, même le générateur intelligent: {str(fallback_error)}")
            return {"error": f"Erreur générale : {str(e)}"}

def collect_rh_appreciations(questions_data):
    valid_appreciations = {
        "très insatisfait": 0,
        "insatisfait": 25,
        "satisfait": 75,
        "très satisfait": 100
    }
    appreciations = []

    print("Entrez une appréciation pour chaque question (très insatisfait, insatisfait, satisfait, très satisfait).")
    for q in questions_data["questions"]:
        while True:
            print(f"\nQuestion ({q['category']}) : {q['question']}")
            appreciation = input("Appréciation : ").strip().lower()
            if appreciation in valid_appreciations:
                appreciations.append({
                    "question": q["question"],
                    "category": q["category"],
                    "appreciation": appreciation,
                    "score": valid_appreciations[appreciation]
                })
                break
            print("Entrée invalide. Options : très insatisfait, insatisfait, satisfait, très satisfait.")

    return appreciations

def generate_predictive_analysis(job_description, cv_data, score_result, questions_data, appreciations_data=None, model="gemini-1.5-flash", max_attempts=3):
    try:
        if not job_description or "error" in cv_data or "error" in score_result or not questions_data:
            return {"error": "Données manquantes ou invalides."}

        gen_model = genai.GenerativeModel(model)

        # Utiliser les appréciations transmises ou les collecter interactivement
        if appreciations_data:
            appreciations = appreciations_data
        else:
            appreciations = collect_rh_appreciations(questions_data)

        interview_score = [a["score"] for a in appreciations]
        interview_avg = sum(interview_score) / len(interview_score)
        culture_scores = [a["score"] for a in appreciations if a["category"] == "Company Culture"]
        culture_avg = sum(culture_scores) / len(culture_scores) if culture_scores else 50.0

        job_title = job_description.get("title", "Développeur Python")
        job_skills = ", ".join(job_description.get("skills", []))
        required_years = job_description.get("required_experience_years", 3)
        cv_skills = ", ".join(cv_data.get("Compétences", []))
        cv_education = cv_data.get("Formations", [{}])[0].get("diplôme", "Non spécifié")
        scores = score_result
        company_context = "TechNova valorise l’innovation, la collaboration, la transparence, et l’impact client."

        prompt = f"""
        Effectuez une analyse des risques et recommandations d’onboarding pour un candidat au poste de {job_title}.
        Données :
        - Fiche de poste : Compétences ({job_skills}), {required_years} ans d’expérience.
        - CV : Compétences ({cv_skills}), Formation ({cv_education}).
        - Scores : Compétences ({scores.get('skills_score', 0):.1f}%), Expérience ({scores.get('experience_score', 0):.1f}%), Formation ({scores.get('education_score', 0):.1f}%).
        - Note d’entretien : {interview_avg:.1f}% (basée sur appréciations RH).
        Retournez un JSON avec :
        - "risks" (liste de 2-3 risques clés).
        - "recommendations" (liste de 3-5 recommandations d’onboarding : formations, mentoring, objectifs 30/60/90 jours).
        JSON valide uniquement.
        """

        for attempt in range(max_attempts):
            try:
                response = gen_model.generate_content(prompt)
                raw_response = response.text.strip()
                with open("debug_analysis_response.txt", "w", encoding="utf-8") as f:
                    f.write(raw_response)
                print(f"Réponse brute de l’API (tentative {attempt + 1}) : {raw_response[:500]}...")

                json_match = re.search(r'\{[\s\S]*\}', raw_response)
                if not json_match:
                    print(f"Tentative {attempt + 1} : Aucun JSON valide.")
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        continue
                    return {"error": "Aucun JSON valide après plusieurs tentatives."}

                analysis = json.loads(json_match.group(0))
                if not all(key in analysis for key in ["risks", "recommendations"]):
                    print(f"Tentative {attempt + 1} : JSON incomplet.")
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        continue
                    return {"error": "JSON incomplet après plusieurs tentatives."}

                break
            except json.JSONDecodeError as e:
                print(f"Tentative {attempt + 1} : Erreur JSON : {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return {"error": f"Erreur JSON après {max_attempts} tentatives : {str(e)}"}
            except Exception as e:
                print(f"Tentative {attempt + 1} : Erreur : {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return {"error": f"Erreur API après {max_attempts} tentatives : {str(e)}"}

        predictive_score = (
            0.30 * scores.get("skills_score", 0) +
            0.25 * scores.get("experience_score", 0) +
            0.25 * interview_avg +
            0.10 * scores.get("education_score", 0) +
            0.10 * culture_avg
        )

        radar_data = {
            "Compétences": scores.get("skills_score", 0),
            "Expérience": scores.get("experience_score", 0),
            "Formation": scores.get("education_score", 0),
            "Culture": culture_avg,
            "Entretien": interview_avg
        }
        radar_labels = list(radar_data.keys())
        radar_values = list(radar_data.values()) + [radar_data["Compétences"]]
        ideal_values = [100] * len(radar_labels) + [100]
        angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
        angles += angles[:1]
        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, polar=True)
        ax.fill(angles, ideal_values, color='lightgray', alpha=0.3, label='Profil idéal')
        ax.fill(angles, radar_values, color='skyblue', alpha=0.5, label='Candidat')
        ax.plot(angles, radar_values, color='blue', linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(radar_labels)
        ax.set_title("Comparaison Candidat vs Profil Idéal", size=14, y=1.08)
        plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
        plt.savefig("predictive_radar.png")
        plt.close()

        report = {
            "predictive_score": predictive_score,
            "appreciations": appreciations,
            "risks": analysis["risks"],
            "recommendations": analysis["recommendations"],
            "radar_data": radar_data
        }

        with open("predictive_performance_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report
    except Exception as e:
        return {"error": f"Erreur générale : {str(e)}"}

def cleanup_memory():
    """Nettoie la mémoire en libérant les ressources non utilisées."""
    global _model_instance
    
    # Libérer le modèle s'il existe
    if _model_instance is not None:
        del _model_instance
        _model_instance = None
    
    # Libérer la mémoire CUDA si disponible
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Forcer le garbage collector
    gc.collect()

def generate_fallback_questions(job_description, cv_data, score_result):
    """Génère des questions de fallback quand l'API échoue"""
    
    job_title = job_description.get("title", "Développeur")
    job_skills = job_description.get("skills", [])
    cv_skills = cv_data.get("Compétences", [])
    cv_education = cv_data.get("Formations", [{}])[0].get("diplôme", "Formation non spécifiée")
    
    # Questions techniques basées sur le poste
    job_questions = [
        {"category": "Job Description", "question": f"Pouvez-vous me parler de votre expérience avec {job_skills[0] if job_skills else 'les technologies principales'} ?", "purpose": "Évaluer compétences techniques"},
        {"category": "Job Description", "question": f"Comment aborderiez-vous un projet complexe en tant que {job_title} ?", "purpose": "Évaluer approche méthodologique"},
        {"category": "Job Description", "question": "Décrivez-moi un défi technique que vous avez récemment résolu et votre approche.", "purpose": "Évaluer résolution de problèmes"},
        {"category": "Job Description", "question": f"Quelles sont selon vous les qualités essentielles d'un bon {job_title} ?", "purpose": "Évaluer compréhension du rôle"},
        {"category": "Job Description", "question": "Comment vous tenez-vous informé des dernières tendances dans votre domaine ?", "purpose": "Évaluer curiosité technique"},
    ]
    
    # Questions culture d'entreprise
    culture_questions = [
        {"category": "Company Culture", "question": "Comment définiriez-vous l'innovation dans votre travail quotidien ?", "purpose": "Évaluer esprit d'innovation"},
        {"category": "Company Culture", "question": "Décrivez une situation où vous avez dû collaborer étroitement avec une équipe.", "purpose": "Évaluer collaboration"},
        {"category": "Company Culture", "question": "Comment gérez-vous la communication dans un environnement de travail transparent ?", "purpose": "Évaluer transparence"},
        {"category": "Company Culture", "question": "Donnez-moi un exemple de comment vous avez amélioré l'expérience d'un client/utilisateur.", "purpose": "Évaluer orientation client"},
        {"category": "Company Culture", "question": "Comment vous adaptez-vous aux changements rapides dans un environnement startup ?", "purpose": "Évaluer adaptabilité"},
    ]
    
    # Questions CV/Expérience personnalisées
    cv_questions = []
    if cv_skills:
        cv_questions.append({"category": "CV/Professional Life", "question": f"Je vois que vous maîtrisez {cv_skills[0]}. Pouvez-vous me donner un exemple concret d'utilisation ?", "purpose": "Approfondir compétences"})
    else:
        cv_questions.append({"category": "CV/Professional Life", "question": "Parlez-moi de vos principales compétences techniques.", "purpose": "Identifier compétences"})
    
    cv_questions.extend([
        {"category": "CV/Professional Life", "question": f"Votre formation en {cv_education} vous a-t-elle préparé à ce rôle ? Comment ?", "purpose": "Évaluer formation"},
        {"category": "CV/Professional Life", "question": "Décrivez-moi le projet dont vous êtes le plus fier dans votre parcours.", "purpose": "Comprendre réalisations"},
        {"category": "CV/Professional Life", "question": "Quels sont vos objectifs de carrière à moyen terme ?", "purpose": "Mesurer ambition"},
        {"category": "CV/Professional Life", "question": "Comment évaluez-vous votre progression professionnelle jusqu'à présent ?", "purpose": "Auto-évaluation"},
    ])
    
    all_questions = job_questions + culture_questions + cv_questions
    
    return {"questions": all_questions}