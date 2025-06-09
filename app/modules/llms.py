# -*- coding: utf-8 -*-
import os
import time
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

try:
    # Configuration de l'API Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
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
        model = genai.GenerativeModel('gemini-pro')
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
        skills_score = 0.0
        experience_score = 0.0
        education_score = 0.0       
        cv_skills = cv_data.get("Compétences", [])
        job_skills = job_description.get("skills", [])
        
        if cv_skills and job_skills:
            # Utiliser get_embeddings avec conversion en tenseur PyTorch
            cv_embeddings = torch.tensor(get_embeddings(cv_skills))
            job_embeddings = torch.tensor(get_embeddings(job_skills))
            
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

        cv_experiences = cv_data.get("Expériences professionnelles", [])
        required_years = job_description.get("required_experience_years", 0)
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
            experience_score = min(total_years / required_years, 1.0) if required_years > 0 else 0.0

        cv_educations = cv_data.get("Formations", [])
        required_degree = job_description.get("required_degree", "")
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

        final_score = (0.5 * skills_score + 0.3 * experience_score + 0.2 * education_score) * 100

        return {
            "skills_score": skills_score * 100,
            "experience_score": experience_score * 100,
            "education_score": education_score * 100,
            "final_score": final_score
        }
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
            response = gen_model.generate_content(prompt)
            raw_response = response.text.strip()
            with open(f"debug_response_{category}.txt", "w", encoding="utf-8") as f:
                f.write(raw_response)
            print(f"Réponse brute pour {category} (tentative {attempt + 1}): {raw_response[:500]}...")

            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if not json_match:
                print(f"Tentative {attempt + 1} ({category}): Aucun JSON valide.")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return None

            questions_data = json.loads(json_match.group(0))
            questions = questions_data.get("questions", [])
            if len(questions) != 5:
                print(f"Tentative {attempt + 1} ({category}): {len(questions)} questions reçues.")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                return None

            return questions
        except json.JSONDecodeError as e:
            print(f"Tentative {attempt + 1} ({category}): Erreur JSON : {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"Tentative {attempt + 1} ({category}): Erreur : {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            return None
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
            Générez 5 questions d'entretien pour un poste de {job_title} (compétences: {job_skills}, {required_years} ans d'expérience).
            Retournez un JSON avec "questions": liste de 5 objets (category: "Job Description", question, purpose).
            JSON valide uniquement.
            """,
            "Company_Culture": f"""
            Générez 5 questions d'entretien sur la culture d'entreprise chez TechNova ({company_context}).
            Retournez un JSON avec "questions": liste de 5 objets (category: "Company Culture", question, purpose).
            JSON valide uniquement.
            """,
            "CV_Professional_Life": f"""
            Générez 5 questions d'entretien basées sur le CV (compétences: {cv_skills}, formation: {cv_education}, score d'expérience: {experience_score:.1f}%).
            Retournez un JSON avec "questions": liste de 5 objets (category: "CV/Professional Life", question, purpose).
            JSON valide uniquement.
            """
        }

        all_questions = []
        for category in prompts:
            questions = generate_questions_for_category(prompts[category], category.replace("/", "_"), model)
            if questions is None:
                return {"error": f"Échec de la génération des questions pour {category}."}
            all_questions.extend(questions)

        if len(all_questions) != 15:
            return {"error": f"Nombre incorrect de questions générées: {len(all_questions)}."}

        questions_data = {"questions": all_questions}

        with open("interview_questions.json", "w", encoding="utf-8") as f:
            json.dump(questions_data, f, indent=2, ensure_ascii=False)

        return questions_data
    except Exception as e:
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

def generate_predictive_analysis(job_description, cv_data, score_result, questions_data, model="gemini-1.5-flash", max_attempts=3):
    try:
        if not job_description or "error" in cv_data or "error" in score_result or not questions_data:
            return {"error": "Données manquantes ou invalides."}

        gen_model = genai.GenerativeModel(model)

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