#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Test simple de l'API
response = requests.get("http://localhost:5000/api/candidates", headers={
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1MjQxMTYxNCwianRpIjoiOTUyNDFiNWQtOGE4ZS00M2UxLTg3NjctMmJhYzk1NjcxYWY0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NTI0MTE2MTQsImNzcmYiOiJiYjgzMGFjOS03YmU0LTQ1ZWMtYjEzYi04NjVhY2U3NDlhNTIiLCJleHAiOjE3NTI0OTgwMTR9.ZPW1SFDJddMukTSvJpz3VsCjGrql7lRw-rZz0hTB1dc'
})

data = response.json()
print(f"📊 Nombre de candidats: {len(data)}")

for i, candidate in enumerate(data):
    print(f"\n👤 Candidat {i+1}: {candidate.get('name', 'N/A')}")
    
    # Vérifier les recommandations
    recs = candidate.get('recommendations')
    risks = candidate.get('risks')
    
    print(f"   📋 Recommandations: {type(recs)} - {len(recs) if recs else 0}")
    print(f"   ⚠️  Risques: {type(risks)} - {len(risks) if risks else 0}")
    
    if recs and len(recs) > 0:
        print(f"   📋 Première rec: {recs[0]}")
    
    if risks and len(risks) > 0:
        print(f"   ⚠️  Premier risque: {risks[0]}")
