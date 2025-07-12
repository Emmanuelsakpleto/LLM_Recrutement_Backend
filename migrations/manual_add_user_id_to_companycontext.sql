-- Migration SQL : Ajout du champ user_id à la table company_context
ALTER TABLE company_context ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1;
ALTER TABLE company_context ADD CONSTRAINT fk_companycontext_user FOREIGN KEY(user_id) REFERENCES "user"(id);
-- (Optionnel) Supprimer la valeur par défaut si besoin :
-- ALTER TABLE company_context ALTER COLUMN user_id DROP DEFAULT;
