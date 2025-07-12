# -*- coding: utf-8 -*-
"""
Service de gestion du processus de recrutement
"""

from .constants import CANDIDATE_STATUS, PROCESS_STAGES, SCORING_THRESHOLDS, SCORING_WEIGHTS
from .models import Candidate
from . import db
import json
import logging

logger = logging.getLogger(__name__)

class ProcessManager:
    """Gestionnaire du processus de recrutement"""
    
    @staticmethod
    def update_candidate_stage(candidate_id, new_stage, new_status):
        """Met à jour l'étape et le statut d'un candidat"""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {"error": "Candidat non trouvé"}
            
            candidate.process_stage = new_stage
            candidate.status = new_status
            db.session.commit()
            
            logger.info(f"Candidat {candidate_id} mis à jour: {new_stage} / {new_status}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Erreur mise à jour candidat {candidate_id}: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def calculate_final_predictive_score(candidate_id):
        """Calcule le score prédictif final après évaluation complète"""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {"error": "Candidat non trouvé"}
            
            # Vérifier que tous les scores sont disponibles
            if candidate.culture_score == 0 or candidate.interview_score == 0:
                return {"error": "Évaluation incomplète"}
            
            # Calculer le score prédictif final
            final_score = (
                candidate.skills_score * SCORING_WEIGHTS['SKILLS'] +
                candidate.experience_score * SCORING_WEIGHTS['EXPERIENCE'] +
                candidate.education_score * SCORING_WEIGHTS['EDUCATION'] +
                candidate.culture_score * SCORING_WEIGHTS['CULTURE'] +
                candidate.interview_score * SCORING_WEIGHTS['INTERVIEW']
            )
            
            # Mettre à jour le candidat
            candidate.final_predictive_score = final_score
            candidate.predictive_score = final_score  # Rétrocompatibilité
            candidate.process_stage = PROCESS_STAGES['FINAL_EVALUATION']
            candidate.status = CANDIDATE_STATUS['FULLY_EVALUATED']
            
            db.session.commit()
            
            logger.info(f"Score prédictif final calculé pour candidat {candidate_id}: {final_score:.2f}%")
            return {"success": True, "final_score": final_score}
            
        except Exception as e:
            logger.error(f"Erreur calcul score final candidat {candidate_id}: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def get_candidate_stage_info(candidate_id):
        """Retourne les informations sur l'étape actuelle du candidat"""
        try:
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return {"error": "Candidat non trouvé"}
            
            # Déterminer les actions disponibles selon l'étape
            actions = []
            next_stage = None
            
            if candidate.process_stage == PROCESS_STAGES['CV_ANALYSIS']:
                actions.append("Générer questions d'entretien")
                next_stage = PROCESS_STAGES['INTERVIEW_QUESTIONS']
            
            elif candidate.process_stage == PROCESS_STAGES['INTERVIEW_QUESTIONS']:
                actions.append("Évaluer entretien")
                next_stage = PROCESS_STAGES['INTERVIEW_EVALUATION']
            
            elif candidate.process_stage == PROCESS_STAGES['INTERVIEW_EVALUATION']:
                actions.append("Calculer score final")
                next_stage = PROCESS_STAGES['FINAL_EVALUATION']
            
            elif candidate.process_stage == PROCESS_STAGES['FINAL_EVALUATION']:
                actions.append("Exporter rapport")
                actions.append("Prendre décision")
            
            return {
                "current_stage": candidate.process_stage,
                "status": candidate.status,
                "actions": actions,
                "next_stage": next_stage,
                "scores": {
                    "skills": candidate.skills_score,
                    "experience": candidate.experience_score,
                    "education": candidate.education_score,
                    "culture": candidate.culture_score,
                    "interview": candidate.interview_score,
                    "final_predictive": candidate.final_predictive_score
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur info étape candidat {candidate_id}: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recommendation_from_score(final_score):
        """Retourne une recommandation basée sur le score final"""
        if final_score >= SCORING_THRESHOLDS['EXCELLENT']:
            return {
                "level": "Excellent",
                "color": "green",
                "recommendation": "Candidat exceptionnel - Recommandation forte d'embauche",
                "actions": ["Préparer offre d'emploi", "Négocier conditions"]
            }
        elif final_score >= SCORING_THRESHOLDS['GOOD']:
            return {
                "level": "Bon",
                "color": "blue",
                "recommendation": "Bon candidat - Recommandation d'embauche",
                "actions": ["Entretien final", "Vérifier références"]
            }
        elif final_score >= SCORING_THRESHOLDS['AVERAGE']:
            return {
                "level": "Moyen",
                "color": "yellow",
                "recommendation": "Candidat correct - À considérer selon les besoins",
                "actions": ["Entretien supplémentaire", "Comparer avec autres candidats"]
            }
        else:
            return {
                "level": "Faible",
                "color": "red",
                "recommendation": "Candidat en dessous des attentes - Déconseillé",
                "actions": ["Envoyer refus poli", "Garder en base pour futurs postes"]
            }
