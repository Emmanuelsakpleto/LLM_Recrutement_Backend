"""
Service de calcul des scores pour le système de recrutement TheRecruit
Gère les 5 dimensions de scoring : Compétences, Expérience, Formation, Culture, Entretien
"""
import json
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class ScoringService:
    """Service centralisé pour tous les calculs de scores"""
    
    # Poids pour le calcul du score prédictif final
    FINAL_WEIGHTS = {
        'skills': 0.30,      # 30% - Compétences techniques
        'experience': 0.25,   # 25% - Expérience professionnelle
        'education': 0.15,    # 15% - Formation
        'culture': 0.15,      # 15% - Adéquation culturelle
        'interview': 0.15     # 15% - Performance en entretien
    }
    
    @staticmethod
    def calculate_cv_scores(cv_data: Dict, job_description: Dict) -> Dict[str, float]:
        """
        Calcule les scores CV (compétences, expérience, formation)
        Retourne les scores de 0 à 100
        """
        from .llms import calculate_cv_score
        
        # Utiliser la fonction existante mais restructurer la sortie
        raw_scores = calculate_cv_score(cv_data, job_description)
        
        if "error" in raw_scores:
            logger.error(f"Erreur calcul scores CV: {raw_scores['error']}")
            return {
                'skills_score': 0.0,
                'experience_score': 0.0,
                'education_score': 0.0
            }
        
        return {
            'skills_score': raw_scores.get('skills_score', 0.0),
            'experience_score': raw_scores.get('experience_score', 0.0),
            'education_score': raw_scores.get('education_score', 0.0)
        }
    
    @staticmethod
    def calculate_culture_score(appreciations: List[Dict], company_context: Dict) -> float:
        """
        Calcule le score d'adéquation culturelle basé sur les réponses aux questions culture
        """
        culture_questions = [q for q in appreciations if q.get('category') == 'Company Culture']
        
        if not culture_questions:
            return 0.0
        
        # Moyenne des scores des questions culture
        total_score = sum(q.get('score', 0) for q in culture_questions)
        avg_score = total_score / len(culture_questions)
        
        # Convertir sur 100 (les scores sont de 1 à 5)
        culture_score = (avg_score / 5.0) * 100
        
        logger.info(f"📊 Culture score: {culture_score}% (basé sur {len(culture_questions)} questions)")
        return culture_score
    
    @staticmethod
    def calculate_interview_score(appreciations: List[Dict]) -> float:
        """
        Calcule le score global d'entretien (toutes catégories sauf culture)
        """
        interview_questions = [q for q in appreciations if q.get('category') != 'Company Culture']
        
        if not interview_questions:
            return 0.0
        
        # Moyenne pondérée par catégorie
        category_scores = {}
        category_counts = {}
        
        for q in interview_questions:
            category = q.get('category', 'Other')
            score = q.get('score', 0)
            
            if category not in category_scores:
                category_scores[category] = 0
                category_counts[category] = 0
            
            category_scores[category] += score
            category_counts[category] += 1
        
        # Calculer la moyenne par catégorie puis la moyenne générale
        category_averages = []
        for category in category_scores:
            avg = category_scores[category] / category_counts[category]
            category_averages.append(avg)
        
        if not category_averages:
            return 0.0
        
        interview_score = (sum(category_averages) / len(category_averages) / 5.0) * 100
        
        logger.info(f"📊 Interview score: {interview_score}% (basé sur {len(interview_questions)} questions)")
        return interview_score
    
    @staticmethod
    def calculate_final_predictive_score(scores: Dict[str, float]) -> float:
        """
        Calcule le score prédictif final basé sur les 5 dimensions
        """
        final_score = 0.0
        
        for dimension, weight in ScoringService.FINAL_WEIGHTS.items():
            score_key = f"{dimension}_score"
            score = scores.get(score_key, 0.0)
            final_score += score * weight
        
        logger.info(f"🏆 Score prédictif final: {final_score}%")
        logger.info(f"   Détail: {scores}")
        
        return final_score
    
    @staticmethod
    def get_candidate_recommendation(final_score: float, scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Génère des recommandations basées sur le score final et les scores détaillés
        """
        recommendations = []
        risks = []
        decision = "À évaluer"
        
        # Analyse globale
        if final_score >= 80:
            decision = "Fortement recommandé"
            recommendations.append("Candidat excellent, procéder à l'embauche")
        elif final_score >= 65:
            decision = "Recommandé"
            recommendations.append("Bon candidat, procéder aux étapes finales")
        elif final_score >= 50:
            decision = "À considérer"
            recommendations.append("Candidat moyen, évaluer selon les besoins")
        else:
            decision = "Non recommandé"
            risks.append("Score global insuffisant pour le poste")
        
        # Analyse détaillée par dimension
        weak_areas = []
        strong_areas = []
        
        for dimension, score in scores.items():
            dimension_name = dimension.replace('_score', '').title()
            if score < 40:
                weak_areas.append(dimension_name)
                risks.append(f"{dimension_name} insuffisant ({score:.1f}%)")
            elif score >= 75:
                strong_areas.append(dimension_name)
                recommendations.append(f"Excellent en {dimension_name} ({score:.1f}%)")
        
        # Recommandations spécifiques
        if weak_areas:
            recommendations.append(f"Formation recommandée en: {', '.join(weak_areas)}")
        
        if strong_areas:
            recommendations.append(f"Points forts à valoriser: {', '.join(strong_areas)}")
        
        return {
            "decision": decision,
            "recommendations": recommendations,
            "risks": risks,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas
        }

    @staticmethod
    def get_process_stage_label(stage: str) -> str:
        """Retourne le libellé français du stade du processus"""
        stages = {
            'cv_analysis': 'Analyse CV',
            'interview_questions_generated': 'Questions générées', 
            'interview_evaluated': 'Entretien évalué',
            'final_assessment': 'Évaluation finale'
        }
        return stages.get(stage, stage)
