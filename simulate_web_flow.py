"""
Simula o fluxo da interface web
"""
import os
import sys
import uuid
import shutil
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Brand
from modules.real_scanner import verificacao_imagem_real
from werkzeug.utils import secure_filename

with app.app_context():
    print("=" * 70)
    print("SIMULANDO O FLUXO DA INTERFACE WEB")
    print("=" * 70)
    
    # Pega a marca NIKE
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if not nike or not nike.logo_path:
        print("❌ Marca NIKE não encontrada ou sem logo")
        exit()
    
    print(f"\n1️⃣  Marca existente: {nike.name}")
    print(f"   Logo: {nike.logo_path}")
    
    # Encontra o arquivo original
    logo_original = None
    for search_dir in ['static/uploads', 'uploads']:
        path = os.path.join(search_dir, nike.logo_path)
        if os.path.exists(path):
            logo_original = path
            print(f"   Arquivo encontrado: {path} ✅")
            break
    
    if not logo_original:
        print("❌ Arquivo original não encontrado")
        exit()
    
    # Simula o upload: cria arquivo temporário
    print(f"\n2️⃣  Simulando upload da interface...")
    filename = secure_filename(f"temp_{uuid.uuid4().hex[:8]}.png")
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Copia o arquivo (simula upload)
    shutil.copy2(logo_original, temp_path)
    print(f"   Temp file criado: {temp_path}")
    print(f"   Temp file existe? {os.path.exists(temp_path)} ✅")
    
    try:
        # Executa a verificação (igual à interface web)
        print(f"\n3️⃣  Executando verificacao_imagem_real()...")
        resultados = verificacao_imagem_real(temp_path, "NIKE")
        
        print(f"\n4️⃣  Resultados:")
        print(f"   - Métodos utilizados: {len(resultados.get('metodos_utilizados', []))}")
        print(f"   - Análises realizadas: {len(resultados.get('analises', []))}")
        print(f"   - Conflitos encontrados: {len(resultados.get('conflitos_visuais', []))}")
        
        if resultados.get('conflitos_visuais'):
            print(f"\n   ✅ CONFLITOS DETECTADOS:")
            for conf in resultados['conflitos_visuais']:
                print(f"      - {conf['marca_bpi']}: {conf['similaridade_media']}% ({conf['gravidade']})")
        else:
            print(f"\n   ❌ NENHUM CONFLITO DETECTADO!")
            print(f"      Isso é o BUG que estamos investigando.")
        
        if resultados.get('resumo'):
            print(f"\n   📊 Resumo:")
            resumo = resultados['resumo']
            print(f"      - Nível: {resumo.get('nivel_risco_visual')}")
            print(f"      - Risco: {resumo.get('risco_visual')}%")
            print(f"      - Recomendação: {resumo.get('recomendacao')[:80]}...")
        
    finally:
        # Limpa o arquivo temporário (igual à interface)
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"\n5️⃣  Temp file removido ✅")
    
    print("\n" + "=" * 70)
