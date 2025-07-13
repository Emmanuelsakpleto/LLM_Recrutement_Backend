#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Test simple de l'API pour voir les statuts
response = requests.get("http://localhost:5000/api/candidates", headers={
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MjQxMTYxNCwianRpIjoiOTUyNDFiNWQtOGE4ZS00M2UxLTg3NjctMmJhYzk1NjcxYWY0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NTI0MTE2MTQsImNzcmYiOiJiYjgzMGFjOS03YmU0LTQ1ZWMtYjEzYi04NjVhY2U3NDlhNTIiLCJleHAiOjE3NTI0OTgwMTR9.ZPW1SFDJddMukTSvJpz3VsCjGrql7lRw-rZz0hTB1dc'
})

data = response.json()
print(f"📊 Nombre de candidats: {len(data)}")

for i, candidate in enumerate(data):
    print(f"\n👤 Candidat {i+1}: {candidate.get('name', 'N/A')}")
    print(f"   📌 Status: '{candidate.get('status', 'N/A')}'")
    print(f"   🆔 ID: {candidate.get('id', 'N/A')}")
    
    # Vérifier scores pour voir si certains candidats devraient avoir des statuts différents
    final_score = candidate.get('final_predictive_score', candidate.get('score_details', {}).get('final_score', 0))
    print(f"   📈 Score final: {final_score}")

print("\n" + "="*50)
print("📋 Résumé des statuts:")
statuses = {}
for candidate in data:
    status = candidate.get('status', 'N/A')
    statuses[status] = statuses.get(status, 0) + 1

for status, count in statuses.items():
    print(f"   • {status}: {count} candidat(s)")
