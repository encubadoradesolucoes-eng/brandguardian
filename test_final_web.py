"""
Teste final: Upload da imagem bola verde via API simulada
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

# Configurar Flask app context
from app import app, Brand
from modules.real_scanner import verificacao_imagem_real

with app.app_context():
    print("=" * 80)
    print("TESTE FINAL: Upload de 'bola verde' via verificacao_imagem_real")
    print("=" * 80)
    
    # Pega o caminho da imagem bola verde
    bola = Brand.query.filter(Brand.name.ilike('%bola%')).first()
    
    if not bola:
        print("❌ Marca bola verde não encontrada")
        exit()
    
    logo_path = os.path.join('uploads', bola.logo_path)
    
    if not os.path.exists(logo_path):
        print(f"❌ Arquivo não encontrado: {logo_path}")
        exit()
    
    print(f"\n📸 Imagem: {logo_path}")
    print(f"📌 Marca: {bola.name}")
    
    # Executa verificação (simula upload)
    print(f"\n🚀 Executando verificacao_imagem_real...")
    resultado = verificacao_imagem_real(logo_path, "bola verde (teste)")
    
    print(f"\n📊 RESULTADO:")
    print(f"   Total conflitos: {len(resultado.get('conflitos_visuais', []))}")
    
    if resultado.get('conflitos_visuais'):
        for c in resultado['conflitos_visuais']:
            print(f"   ✅ {c['brand_name']}: {c['similarity_final']}% [{c['gravidade']}]")
        print(f"\n🎯 SUCESSO! Sistema detecta duplicatas corretamente!")
    else:
        print(f"   ❌ FALHA! Nenhum conflito detectado")
        print(f"\nResposta completa:")
        import json
        print(json.dumps(resultado, indent=2))
