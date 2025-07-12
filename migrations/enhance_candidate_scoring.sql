-- Migration SQL : Amélioration du système de scoring à 5 dimensions

-- Ajout des champs pour les 5 scores finaux
ALTER TABLE candidate ADD COLUMN skills_score FLOAT DEFAULT 0.0;
ALTER TABLE candidate ADD COLUMN experience_score FLOAT DEFAULT 0.0;
ALTER TABLE candidate ADD COLUMN education_score FLOAT DEFAULT 0.0;
ALTER TABLE candidate ADD COLUMN culture_score FLOAT DEFAULT 0.0;
ALTER TABLE candidate ADD COLUMN interview_score FLOAT DEFAULT 0.0;

-- Ajout des champs pour l'état du processus
ALTER TABLE candidate ADD COLUMN process_stage VARCHAR(50) DEFAULT 'cv_analysis';
-- Valeurs possibles: 'cv_analysis', 'interview_questions_generated', 'interview_evaluated', 'final_assessment'

-- Ajout du score prédictif final (combinaison des 5 scores)
ALTER TABLE candidate ADD COLUMN final_predictive_score FLOAT DEFAULT 0.0;

-- Mettre à jour les candidats existants avec les scores déjà calculés
UPDATE candidate 
SET 
    skills_score = CASE 
        WHEN score_details IS NOT NULL AND score_details != '' THEN 
            CAST(JSON_EXTRACT(score_details, '$.skills_score') AS FLOAT)
        ELSE 0.0 
    END,
    experience_score = CASE 
        WHEN score_details IS NOT NULL AND score_details != '' THEN 
            CAST(JSON_EXTRACT(score_details, '$.experience_score') AS FLOAT)
        ELSE 0.0 
    END,
    education_score = CASE 
        WHEN score_details IS NOT NULL AND score_details != '' THEN 
            CAST(JSON_EXTRACT(score_details, '$.education_score') AS FLOAT)
        ELSE 0.0 
    END,
    final_predictive_score = predictive_score
WHERE score_details IS NOT NULL;

-- Index pour optimiser les requêtes de dashboard
CREATE INDEX idx_candidate_brief_stage ON candidate(brief_id, process_stage);
CREATE INDEX idx_candidate_user_stage ON candidate(user_id, process_stage);
