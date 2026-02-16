import requests
import json

url = "https://brandguardian-1.onrender.com/api/scan-live"

print("TESTE CHOCOLATA")
print("-" * 40)

response = requests.post(url, json={'term': 'chocolata'})
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"BPI count: {data['counts']['bpi']}")
    print(f"BPI data: {data.get('bpi', [])}")
    print(f"\nJSON completo:")
    print(json.dumps(data, indent=2))
else:
    print(f"Erro: {response.text}")
