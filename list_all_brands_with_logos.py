"""
Lista TODAS as marcas com logo e seus hashes
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, Brand
from PIL import Image
import imagehash

with app.app_context():
    print("=" * 80)
    print("TODAS AS MARCAS COM LOGO NO BANCO")
    print("=" * 80)
    
    brands = Brand.query.filter(Brand.logo_path.isnot(None)).all()
    
    print(f"\n📊 Total: {len(brands)} marcas com logo\n")
    
    for i, brand in enumerate(brands, 1):
        print(f"{i}. {brand.name}")
        print(f"   Logo: {brand.logo_path}")
        
        # Tenta encontrar o arquivo
        logo_path = None
        for search_dir in ['static/uploads', 'uploads']:
            path = os.path.join(search_dir, brand.logo_path)
            if os.path.exists(path):
                logo_path = path
                break
        
        if logo_path:
            try:
                img = Image.open(logo_path)
                hash_phash = imagehash.phash(img)
                print(f"   Path: {os.path.abspath(logo_path)}")
                print(f"   Hash: {hash_phash}")
                print(f"   Dimensões: {img.width}x{img.height}")
            except Exception as e:
                print(f"   ⚠️ Erro ao ler: {e}")
        else:
            print(f"   ❌ ARQUIVO NÃO ENCONTRADO!")
        
        print()
