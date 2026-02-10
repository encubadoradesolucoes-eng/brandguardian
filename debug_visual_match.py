"""
Debug da verificação visual - Por que não detectou?
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Brand
from modules.image_matcher import DuplicateImageFinder
from PIL import Image
import imagehash

with app.app_context():
    # Pega a marca NIKE
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if not nike or not nike.logo_path:
        print("❌ Marca NIKE não encontrada ou sem logo")
        exit()
    
    print("=" * 70)
    print("DEBUG: Por que não detectou a mesma imagem?")
    print("=" * 70)
    
    print(f"\n📌 Marca no Banco: {nike.name}")
    print(f"   - Logo Path: {nike.logo_path}")
    
    # Tenta encontrar o arquivo
    app_root = os.path.dirname(__file__)
    possible_paths = [
        os.path.join('static', 'uploads', nike.logo_path),
        os.path.join('uploads', nike.logo_path),
        os.path.join(app_root, 'static', 'uploads', nike.logo_path),
        os.path.join(app_root, 'uploads', nike.logo_path),
    ]
    
    logo_path = None
    for path in possible_paths:
        if os.path.exists(path):
            logo_path = path
            print(f"   - Arquivo encontrado em: {path} ✅")
            break
    
    if not logo_path:
        print(f"   - ⚠️  PROBLEMA 1: Arquivo não encontrado em nenhum caminho!")
        for p in possible_paths:
            print(f"      Tentou: {p}")
        exit()
    
    # Calcula hash do arquivo
    print(f"\n🔐 Calculando hash da imagem no banco...")
    img = Image.open(logo_path)
    hash_avg = imagehash.average_hash(img)
    hash_phash = imagehash.phash(img)
    hash_dhash = imagehash.dhash(img)
    
    print(f"   - Average Hash: {hash_avg}")
    print(f"   - pHash: {hash_phash}")
    print(f"   - dHash: {hash_dhash}")
    
    # Agora testa o DuplicateImageFinder
    print(f"\n🔍 Testando DuplicateImageFinder...")
    finder = DuplicateImageFinder(app_root)
    
    # Usa a MESMA imagem para comparar
    results = finder.find_duplicate_images(
        logo_path,
        threshold=12,
        include_brands=True,
        include_ipi=False
    )
    
    print(f"\n📊 Resultados:")
    print(f"   - Conflitos encontrados: {len(results)}")
    
    if results:
        for r in results:
            print(f"\n   ✅ CONFLITO DETECTADO:")
            print(f"      - Marca: {r['brand_name']}")
            print(f"      - Similaridade Final: {r['similarity_final']}%")
            print(f"      - Similaridade Avg: {r['similarity_avg']}%")
            print(f"      - Similaridade pHash: {r['similarity_phash']}%")
            print(f"      - Similaridade dHash: {r['similarity_dhash']}%")
            print(f"      - Gravidade: {r['gravidade']}")
    else:
        print(f"\n   ⚠️  NENHUM CONFLITO DETECTADO!")
        print(f"\n   🔍 Investigando o porquê...")
        
        # Verifica quantas marcas tem logo
        brands_com_logo = Brand.query.filter(Brand.logo_path.isnot(None)).all()
        print(f"\n   📊 Marcas com logo no banco: {len(brands_com_logo)}")
        
        for b in brands_com_logo:
            print(f"\n   🔎 Testando marca: {b.name}")
            print(f"      - Logo path: {b.logo_path}")
            
            # Tenta resolver o caminho
            for search_dir in ['static/uploads', 'uploads']:
                test_path = os.path.join(app_root, search_dir, b.logo_path)
                exists = os.path.exists(test_path)
                print(f"      - {search_dir}/{b.logo_path}: {'✅' if exists else '❌'}")
                
                if exists:
                    # Compara os hashes
                    try:
                        img_b = Image.open(test_path)
                        hash_b_avg = imagehash.average_hash(img_b)
                        hash_b_phash = imagehash.phash(img_b)
                        hash_b_dhash = imagehash.dhash(img_b)
                        
                        dist_avg = hash_avg - hash_b_avg
                        dist_phash = hash_phash - hash_b_phash
                        dist_dhash = hash_dhash - hash_b_dhash
                        
                        print(f"      - Distância Avg: {dist_avg}")
                        print(f"      - Distância pHash: {dist_phash}")
                        print(f"      - Distância dHash: {dist_dhash}")
                        print(f"      - Menor distância: {min(dist_avg, dist_phash, dist_dhash)}")
                        print(f"      - Passa threshold 12? {min(dist_avg, dist_phash, dist_dhash) <= 12}")
                    except Exception as e:
                        print(f"      - Erro ao comparar: {e}")
    
    print("\n" + "=" * 70)
