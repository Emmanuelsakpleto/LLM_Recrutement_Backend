# Test des endpoints de l'API TechNovaRH
Write-Host "Tests de l'API TechNovaRH" -ForegroundColor Green

# Configuration
$baseUrl = "http://localhost:5000"
$token = ""  # À remplir après la connexion

# 1. Test de connexion et récupération du token
Write-Host "`n1. Test de connexion" -ForegroundColor Cyan
$loginBody = @{
    username = "admin"
    password = "TechNova2025"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
    $token = $loginResponse.token
    Write-Host "✓ Connexion réussie" -ForegroundColor Green
    Write-Host "Token obtenu: $($token.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Échec de la connexion: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Headers avec le token pour les requêtes authentifiées
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
}

# 2. Création d'une fiche de poste
Write-Host "`n2. Test de création d'une fiche de poste" -ForegroundColor Cyan
$briefBody = @{
    title = "Développeur Python Senior"
    skills = "Python, Flask, SQL, API REST, Docker"
    experience = "5"
    description = "Nous recherchons un développeur Python senior pour notre équipe backend, spécialisé dans le développement API REST et bases de données."
} | ConvertTo-Json

try {
    $briefResponse = Invoke-RestMethod -Uri "$baseUrl/api/job-briefs" -Method Post -Headers $headers -Body $briefBody
    Write-Host "✓ Fiche de poste créée" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $briefResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la création de la fiche de poste: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Récupération de la fiche de poste
Write-Host "`n3. Test de récupération de la fiche de poste" -ForegroundColor Cyan
try {
    $getBriefResponse = Invoke-RestMethod -Uri "$baseUrl/api/job-briefs" -Method Get
    Write-Host "✓ Fiche de poste récupérée" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $getBriefResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la récupération de la fiche de poste: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Test d'envoi d'un CV (nécessite un fichier PDF)
Write-Host "`n4. Test d'envoi d'un CV" -ForegroundColor Cyan
Write-Host "Note: Pour tester cette partie, placez un fichier CV.pdf dans le dossier" -ForegroundColor Yellow
if (Test-Path "CV.pdf") {
    $filePath = "CV.pdf"
    $form = @{
        file = Get-Item -Path $filePath
    }
    try {
        $cvResponse = Invoke-RestMethod -Uri "$baseUrl/api/cv" -Method Post -Form $form
        Write-Host "✓ CV envoyé et analysé" -ForegroundColor Green
        Write-Host "Réponse:" -ForegroundColor Gray
        $cvResponse | ConvertTo-Json -Depth 3
    } catch {
        Write-Host "✗ Échec de l'envoi du CV: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Fichier CV.pdf non trouvé" -ForegroundColor Red
}

# 5. Test de création du contexte d'entreprise
Write-Host "`n5. Test de création du contexte d'entreprise" -ForegroundColor Cyan
$contextBody = @{
    values = @("Innovation", "Collaboration", "Excellence")
    culture = "Startup dynamique axée sur l'innovation et l'impact client"
} | ConvertTo-Json

try {
    $contextResponse = Invoke-RestMethod -Uri "$baseUrl/api/context" -Method Post -Headers $headers -Body $contextBody
    Write-Host "✓ Contexte d'entreprise créé" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $contextResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la création du contexte: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. Récupération des questions d'entretien
Write-Host "`n6. Test de récupération des questions d'entretien" -ForegroundColor Cyan
try {
    $questionsResponse = Invoke-RestMethod -Uri "$baseUrl/api/context/questions" -Method Get
    Write-Host "✓ Questions récupérées" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $questionsResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la récupération des questions: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. Test de soumission d'une évaluation
Write-Host "`n7. Test de soumission d'une évaluation" -ForegroundColor Cyan
$evaluationBody = @{
    appreciations = @(
        @{
            question = "Question test"
            category = "Test Category"
            appreciation = "satisfait"
            score = 75
        }
    )
} | ConvertTo-Json

try {
    $evaluationResponse = Invoke-RestMethod -Uri "$baseUrl/api/evaluation/1" -Method Post -Headers $headers -Body $evaluationBody
    Write-Host "✓ Évaluation soumise" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $evaluationResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la soumission de l'évaluation: $($_.Exception.Message)" -ForegroundColor Red
}

# 8. Récupération des candidats
Write-Host "`n8. Test de récupération des candidats" -ForegroundColor Cyan
try {
    $candidatesResponse = Invoke-RestMethod -Uri "$baseUrl/api/candidates" -Method Get -Headers $headers
    Write-Host "✓ Liste des candidats récupérée" -ForegroundColor Green
    Write-Host "Réponse:" -ForegroundColor Gray
    $candidatesResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Échec de la récupération des candidats: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTests terminés" -ForegroundColor Green
