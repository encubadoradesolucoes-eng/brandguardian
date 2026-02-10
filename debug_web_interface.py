"""
Debug: Por que a interface web não detecta mas o teste detecta?
"""
import os
import sys
import shutil
import uuid
sys.path.insert(0, os.path.dirname(__file__))

from app import app, Brand
from modules.image_matcher import DuplicateImageFinder
from werkzeug.utils import secure_filename
from PIL import Image
import imagehash

with app.app_context():
    print("=" * 80)
    print("COMPARAÇÃO: TESTE vs INTERFACE WEB")
    print("=" * 80)
    
    # Pega a marca NIKE
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if not nike:
        print("❌ Marca NIKE não encontrada")
        exit()
    
    print(f"\n📌 Marca no banco: {nike.name}")
    print(f"   Logo Path: {nike.logo_path}")
    
    # Encontra o arquivo
    logo_original = None
    for search_dir in ['static/uploads', 'uploads']:
        path = os.path.join(search_dir, nike.logo_path)
        if os.path.exists(path):
            logo_original = path
            print(f"   Arquivo: {path}")
            break
    
    if not logo_original:
        print("❌ Arquivo não encontrado")
        exit()
    
    # Calcula hash do arquivo original
    img = Image.open(logo_original)
    hash_orig_avg = imagehash.average_hash(img)
    hash_orig_phash = imagehash.phash(img)
    hash_orig_dhash = imagehash.dhash(img)
    
    print(f"\n🔐 Hashes do arquivo original no banco:")
    print(f"   Avg:   {hash_orig_avg}")
    print(f"   pHash: {hash_orig_phash}")
    print(f"   dHash: {hash_orig_dhash}")
    
    # Simula o que a interface web faz
    print(f"\n" + "─" * 80)
    print("SIMULANDO INTERFACE WEB")
    print("─" * 80)
    
    # Cria temp file como a interface faz
    filename = secure_filename(f"temp_{uuid.uuid4().hex[:8]}.png")
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(f"\n1. Criando arquivo temporário: {temp_path}")
    shutil.copy2(logo_original, temp_path)
    
    # Verifica hash do temp
    img_temp = Image.open(temp_path)
    hash_temp_avg = imagehash.average_hash(img_temp)
    hash_temp_phash = imagehash.phash(img_temp)
    hash_temp_dhash = imagehash.dhash(img_temp)
    
    print(f"\n🔐 Hashes do arquivo temporário:")
    print(f"   Avg:   {hash_temp_avg}")
    print(f"   pHash: {hash_temp_phash}")
    print(f"   dHash: {hash_temp_dhash}")
    
    print(f"\n✅ Hashes são idênticos? {hash_orig_phash == hash_temp_phash}")
    
    # Testa o DuplicateImageFinder
    print(f"\n2. Executando DuplicateImageFinder...")
    print(f"   Target: {temp_path}")
    print(f"   Caminho absoluto? {os.path.isabs(temp_path)}")
    print(f"   Arquivo existe? {os.path.exists(temp_path)}")
    
    app_root = os.path.dirname(__file__)
    finder = DuplicateImageFinder(app_root)
    
    print(f"\n   Base path do finder: {finder.base_path}")
    print(f"   Marcas no banco: {Brand.query.filter(Brand.logo_path.isnot(None)).count()}")
    
    # Testa _resolve_logo_path para a marca NIKE
    print(f"\n3. Testando resolução do logo da NIKE:")
    resolved = finder._resolve_logo_path(nike.logo_path, ['static/uploads', 'uploads'])
    print(f"   Input: {nike.logo_path}")
    print(f"   Resolved: {resolved}")
    print(f"   Existe? {os.path.exists(resolved) if resolved else 'N/A'}")
    
    # Executa a busca
    print(f"\n4. Executando busca completa...")
    results = finder.find_duplicate_images(
        temp_path,
        threshold=12,
        include_brands=True,
        include_ipi=False
    )
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Conflitos encontrados: {len(results)}")
    
    if results:
        for r in results:
            print(f"\n   ✅ CONFLITO:")
            print(f"      Marca: {r['brand_name']}")
            print(f"      Similaridade: {r['similarity_final']}%")
            print(f"      Logo URL: {r['logo_url']}")
    else:
        print(f"\n   ❌ NENHUM CONFLITO!")
        print(f"\n   🔍 DEBUG: Vamos verificar manualmente...")
        
        # Debug manual
        brands = Brand.query.filter(Brand.logo_path.isnot(None)).all()
        print(f"\n   Marcas com logo: {len(brands)}")
        
        for b in brands:
            print(f"\n   🔎 Marca: {b.name}")
            print(f"      Logo path: {b.logo_path}")
            
            resolved = finder._resolve_logo_path(b.logo_path, ['static/uploads', 'uploads'])
            print(f"      Resolved: {resolved}")
            print(f"      Existe? {os.path.exists(resolved) if resolved else False}")
            
            if resolved and os.path.exists(resolved):
                # Compara manualmente
                img_b = Image.open(resolved)
                hash_b_phash = imagehash.phash(img_b)
                
                dist = hash_temp_phash - hash_b_phash
                print(f"      Hash: {hash_b_phash}")
                print(f"      Distância: {dist}")
                print(f"      Deveria detectar? {dist <= 12}")
                
                if dist <= 12:
                    print(f"      ⚠️  DEVERIA TER DETECTADO!")
    
    # Limpa
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    print(f"\n" + "=" * 80)
