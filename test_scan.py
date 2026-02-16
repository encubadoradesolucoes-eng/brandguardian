import requests
import json

# Testar a API de scan
url = "https://brandguardian-1.onrender.com/api/scan-live"

# Teste 1: Cartrack (sabemos que existe)
print("=" * 60)
print("TESTE 1: CARTRACK")
print("=" * 60)

response = requests.post(url, json={'term': 'cartrack'})
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResultados:")
    print(f"  - Domínios: {data['counts']['domains']}")
    print(f"  - Social: {data['counts']['social']}")
    print(f"  - Local (M24): {data['counts']['local']}")
    print(f"  - BPI (IPI): {data['counts']['bpi']}")
    
    if data['counts']['bpi'] > 0:
        print(f"\n✅ BPI ENCONTROU {data['counts']['bpi']} resultados!")
        if 'bpi' in data and len(data['bpi']) > 0:
            print(f"  Detalhes: {data['bpi']}")
        else:
            print(f"  ⚠️ MAS NÃO RETORNOU OS DETALHES (precisa login?)")
    else:
        print(f"\n❌ BPI NÃO ENCONTROU NADA!")
else:
    print(f"Erro: {response.text}")

print("\n" + "=" * 60)
print("TESTE 2: CHOCOLATA")
print("=" * 60)

response = requests.post(url, json={'term': 'chocolata'})
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResultados:")
    print(f"  - Domínios: {data['counts']['domains']}")
    print(f"  - Social: {data['counts']['social']}")
    print(f"  - Local (M24): {data['counts']['local']}")
    print(f"  - BPI (IPI): {data['counts']['bpi']}")
    
    if data['counts']['bpi'] > 0:
        print(f"\n✅ BPI ENCONTROU {data['counts']['bpi']} resultados!")
        if 'bpi' in data and len(data['bpi']) > 0:
            print(f"  Detalhes: {data['bpi']}")
        else:
            print(f"  ⚠️ MAS NÃO RETORNOU OS DETALHES (precisa login?)")
    else:
        print(f"\n❌ BPI NÃO ENCONTROU NADA!")
else:
    print(f"Erro: {response.text}")

print("\n" + "=" * 60)
print("CONCLUSÃO")
print("=" * 60)
print("Se BPI count > 0 mas não mostra detalhes: problema de autenticação")
print("Se BPI count = 0: problema na query do banco de dados")
