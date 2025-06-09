$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZS..."  # Remplacez par votre token complet

$headers = @{
    'Content-Type' = 'application/json'
    'Authorization' = "Bearer $token"
}

$body = @{
    title = 'Développeur Python Senior'
    skills = 'Python, Flask, SQL, API REST'
    experience = '5'
    description = 'Nous recherchons un développeur Python senior pour notre équipe backend, spécialisé dans le développement API REST et bases de données.'
}

$jsonBody = $body | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri 'http://localhost:5000/api/job-briefs' -Method Post -Headers $headers -Body $jsonBody
    Write-Host "Response:"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error:"
    Write-Host $_.Exception.Message
    Write-Host "Response:"
    Write-Host $_.ErrorDetails
}
