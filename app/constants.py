# -*- coding: utf-8 -*-
"""
Constantes pour l'application de recrutement
"""

# Statuts des candidats selon le processus
CANDIDATE_STATUS = {
    'CV_UPLOADED': 'CV téléchargé',
    'CV_ANALYZED': 'CV analysé',
    'INTERVIEW_QUESTIONS_GENERATED': 'Questions d\'entretien générées',
    'INTERVIEW_EVALUATED': 'Entretien évalué',
    'FULLY_EVALUATED': 'Évaluation complète',
    'REJECTED': 'Rejeté',
    'ACCEPTED': 'Accepté'
}

# Étapes du processus
PROCESS_STAGES = {
    'UPLOAD': 'upload',
    'CV_ANALYSIS': 'cv_analysis',
    'INTERVIEW_QUESTIONS': 'interview_questions',
    'INTERVIEW_EVALUATION': 'interview_evaluation',
    'FINAL_EVALUATION': 'final_evaluation',
    'COMPLETED': 'completed'
}

# Seuils de scoring
SCORING_THRESHOLDS = {
    'EXCELLENT': 80.0,
    'GOOD': 60.0,
    'AVERAGE': 40.0,
    'POOR': 20.0
}

# Poids des scores dans le calcul du score prédictif final
SCORING_WEIGHTS = {
    'SKILLS': 0.25,      # 25%
    'EXPERIENCE': 0.20,  # 20%
    'EDUCATION': 0.15,   # 15%
    'CULTURE': 0.20,     # 20%
    'INTERVIEW': 0.20    # 20%
}
