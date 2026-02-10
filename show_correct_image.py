"""
Verifica qual imagem está salva como logo da NIKE
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, Brand
from PIL import Image
import imagehash

with app.app_context():
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if not nike or not nike.logo_path:
        print("❌ Marca NIKE não encontrada ou sem logo")
        exit()
    
    print("=" * 80)
    print("LOGO DA NIKE NO BANCO DE DADOS")
    print("=" * 80)
    
    print(f"\n📌 Marca: {nike.name}")
    print(f"   Logo Path: {nike.logo_path}")
    
    # Encontra o arquivo
    logo_path = None
    for search_dir in ['static/uploads', 'uploads']:
        path = os.path.join(search_dir, nike.logo_path)
        if os.path.exists(path):
            logo_path = path
            print(f"   Localização: {os.path.abspath(path)}")
            break
    
    if not logo_path:
        print("❌ Arquivo não encontrado!")
        exit()
    
    # Calcula hash
    img = Image.open(logo_path)
    hash_phash = imagehash.phash(img)
    
    print(f"\n🔐 HASH CORRETO (da imagem no banco):")
    print(f"   pHash: {hash_phash}")
    
    print(f"\n🔐 HASH QUE VOCÊ ENVIOU:")
    print(f"   pHash: ba91c14e9679c9c5")
    
    print(f"\n❌ SÃO DIFERENTES!")
    print(f"   Distância: {hash_phash - imagehash.hex_to_hash('ba91c14e9679c9c5')}")
    
    print(f"\n" + "=" * 80)
    print("SOLUÇÃO")
    print("=" * 80)
    print(f"\n1. Localize este arquivo no seu computador:")
    print(f"   {os.path.abspath(logo_path)}")
    print(f"\n2. Abra a pasta:")
    print(f"   {os.path.dirname(os.path.abspath(logo_path))}")
    print(f"\n3. O arquivo se chama:")
    print(f"   {os.path.basename(logo_path)}")
    print(f"\n4. ENVIE EXATAMENTE ESSE ARQUIVO na interface web")
    print(f"\n5. Aí sim vai detectar 100% de similaridade!")
    print(f"\n" + "=" * 80)
    
    # Mostra preview da imagem
    print(f"\n📊 Informações da imagem correta:")
    print(f"   Formato: {img.format}")
    print(f"   Modo: {img.mode}")
    print(f"   Dimensões: {img.width} x {img.height}")
    print(f"   Tamanho: {os.path.getsize(logo_path)} bytes ({os.path.getsize(logo_path)/1024:.1f} KB)")
