-- Migration SQL : Ajout des champs manquants aux modèles

-- Ajout des champs manquants au modèle JobBrief
ALTER TABLE job_brief ADD COLUMN user_id INTEGER;
ALTER TABLE job_brief ADD COLUMN context_id INTEGER;
ALTER TABLE job_brief ADD CONSTRAINT fk_jobbrief_user FOREIGN KEY(user_id) REFERENCES "user"(id);
ALTER TABLE job_brief ADD CONSTRAINT fk_jobbrief_context FOREIGN KEY(context_id) REFERENCES company_context(id);

-- Ajout des champs manquants au modèle Candidate
ALTER TABLE candidate ADD COLUMN brief_id INTEGER;
ALTER TABLE candidate ADD COLUMN user_id INTEGER;
ALTER TABLE candidate ADD COLUMN interview_questions TEXT;
ALTER TABLE candidate ADD COLUMN score_details TEXT;
ALTER TABLE candidate ADD COLUMN risks TEXT;
ALTER TABLE candidate ADD COLUMN recommendations TEXT;
ALTER TABLE candidate ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE candidate ADD CONSTRAINT fk_candidate_brief FOREIGN KEY(brief_id) REFERENCES job_brief(id);
ALTER TABLE candidate ADD CONSTRAINT fk_candidate_user FOREIGN KEY(user_id) REFERENCES "user"(id);

-- Mettre à jour les enregistrements existants avec des valeurs par défaut
UPDATE job_brief SET user_id = 1 WHERE user_id IS NULL;
UPDATE candidate SET user_id = 1 WHERE user_id IS NULL;

-- Rendre les champs user_id obligatoires
ALTER TABLE job_brief ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE candidate ALTER COLUMN user_id SET NOT NULL;
