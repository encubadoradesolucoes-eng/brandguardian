"""
Gera JSON exatamente como o servidor envia para a interface
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))

from app import app, Brand
from modules.real_scanner import verificacao_imagem_real

with app.app_context():
    # Pega a marca NIKE
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if not nike or not nike.logo_path:
        print("❌ Marca NIKE não encontrada")
        exit()
    
    # Encontra o arquivo
    logo_path = None
    for search_dir in ['static/uploads', 'uploads']:
        path = os.path.join(search_dir, nike.logo_path)
        if os.path.exists(path):
            logo_path = path
            break
    
    if not logo_path:
        print("❌ Arquivo não encontrado")
        exit()
    
    print("🔄 Executando verificacao_imagem_real...")
    resultados = verificacao_imagem_real(logo_path, "NIKE")
    
    # Simula a resposta da API
    response = {
        'status': 'sucesso',
        'resultados': resultados
    }
    
    print("\n" + "=" * 80)
    print("RESPOSTA JSON DO SERVIDOR")
    print("=" * 80)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    print(f"\n📊 RESUMO:")
    print(f"   Status: {response['status']}")
    print(f"   Conflitos: {len(resultados.get('conflitos_visuais', []))}")
    print(f"   Nível risco: {resultados.get('resumo', {}).get('nivel_risco_visual', 'N/A')}")
    
    if resultados.get('conflitos_visuais'):
        print(f"\n⚠️  CONFLITOS DETECTADOS:")
        for conf in resultados['conflitos_visuais']:
            print(f"      - {conf['marca_bpi']}: {conf['similaridade_media']}%")
