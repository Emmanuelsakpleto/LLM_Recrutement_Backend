from app.modules.llms import generate_job_description

test_brief = "Nous recherchons un développeur Python senior pour notre équipe backend"
result = generate_job_description(test_brief)
print("Résultat du test :")
print(result)
