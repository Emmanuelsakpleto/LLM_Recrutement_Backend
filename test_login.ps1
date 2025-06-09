$body = @{
    username = "admin"
    password = "TechNova2025"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "Envoi de la requête avec le corps:"
Write-Host $body
Write-Host "`nHeaders:"
Write-Host ($headers | ConvertTo-Json)

try {
    $response = Invoke-RestMethod `
        -Uri "http://localhost:5000/api/auth/login" `
        -Method Post `
        -Body $body `
        -Headers $headers `
        -ContentType "application/json"

    Write-Host "`nRéponse reçue:"
    $response | ConvertTo-Json
} catch {
    Write-Host "`nErreur:"
    Write-Host $_.Exception.Message
    Write-Host "`nRéponse d'erreur:"
    $rawResponse = $_.ErrorDetails.Message
    Write-Host $rawResponse
}
