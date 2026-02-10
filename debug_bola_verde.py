"""
Debug: Por que não detecta mesmo com hash idêntico?
"""
import os
import sys
import sqlite3
sys.path.insert(0, os.path.dirname(__file__))

from modules.image_matcher import DuplicateImageFinder
from PIL import Image
import imagehash

if True:
    print("=" * 80)
    print("DEBUG: Por que não detecta bola verde?")
    print("=" * 80)
    
    # Conecta no banco
    conn = sqlite3.connect('database/brands.db')
    cursor = conn.cursor()
    
    # Pega a marca bola verde
    cursor.execute("SELECT id, name, logo_path FROM brand WHERE name LIKE '%bola%'")
    row = cursor.fetchone()
    
    if not row:
        print("❌ Marca bola verde não encontrada")
        exit()
    
    brand_id, brand_name, logo_path_db = row
    print(f"\n📌 Marca: {brand_name}")
    print(f"   Logo path no banco: {logo_path_db}")
    
    # Encontra arquivo
    logo_path = None
    for search_dir in ['static/uploads', 'uploads']:
        path = os.path.join(search_dir, logo_path_db)
        if os.path.exists(path):
            logo_path = path
            break
    
    if not logo_path:
        print("❌ Arquivo não encontrado")
        exit()
    
    print(f"   Path completo: {os.path.abspath(logo_path)}")
    
    # Hash da imagem no banco
    img = Image.open(logo_path)
    hash_banco = imagehash.phash(img)
    print(f"   Hash no banco: {hash_banco}")
    
    # Simula o teste (usa a mesma imagem)
    print(f"\n🔍 Testando DuplicateImageFinder...")
    
    app_root = os.path.dirname(__file__)
    finder = DuplicateImageFinder(app_root)
    
    print(f"   Base path: {finder.base_path}")
    print(f"   Target: {logo_path}")
    print(f"   É absoluto? {os.path.isabs(logo_path)}")
    
    # Adiciona logs ao método _resolve_logo_path
    print(f"\n📁 Testando resolução de path para: {logo_path_db}")
    resolved = finder._resolve_logo_path(logo_path_db, ['static/uploads', 'uploads'])
    print(f"   Resolved: {resolved}")
    print(f"   Existe? {os.path.exists(resolved) if resolved else False}")
    
    # Executa busca
    print(f"\n🚀 Executando find_duplicate_images...")
    
    # Prepara lista de brands
    cursor.execute("SELECT id, name, logo_path, owner_name FROM brand WHERE logo_path IS NOT NULL")
    brands = cursor.fetchall()
    brand_records = [{
        'id': b[0],
        'name': b[1],
        'logo_path': b[2],
        'owner_name': b[3]
    } for b in brands]
    
    results = finder.find_duplicate_images(
        logo_path,
        threshold=12,
        brand_records=brand_records,
        ipi_records=[]
    )
    
    print(f"\n📊 RESULTADO:")
    print(f"   Conflitos: {len(results)}")
    
    if results:
        for r in results:
            print(f"   ✅ {r['brand_name']}: {r['similarity_final']}%")
    else:
        print(f"   ❌ NENHUM conflito encontrado - BUG!")
        
        # Debug manual
        print(f"\n🔍 Debug Manual:")
        print(f"   Target path: {logo_path}")
        print(f"   Target é relativo? {not os.path.isabs(logo_path)}")
        
        # Testa comparação direta
        hash_target = imagehash.phash(img)
        dist = hash_banco - hash_target
        print(f"   Hash target: {hash_target}")
        print(f"   Hash banco: {hash_banco}")
        print(f"   Distância: {dist}")
        print(f"   Deveria detectar (dist <= 12)? {dist <= 12}")
    
    conn.close()
