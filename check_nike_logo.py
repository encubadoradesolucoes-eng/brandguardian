"""
Verifica se a marca NIKE tem logo no banco
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Brand

with app.app_context():
    nike = Brand.query.filter(Brand.name.ilike('%NIKE%')).first()
    
    if nike:
        print(f"✅ Marca encontrada: {nike.name}")
        print(f"   - ID: {nike.id}")
        print(f"   - Titular: {nike.owner_name}")
        print(f"   - Logo Path: {nike.logo_path}")
        print(f"   - Logo existe? {'SIM ✅' if nike.logo_path else 'NÃO ❌'}")
        
        if nike.logo_path:
            # Verifica se o arquivo existe fisicamente
            possible_paths = [
                os.path.join('static', 'uploads', nike.logo_path),
                os.path.join('uploads', nike.logo_path),
                nike.logo_path
            ]
            
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"   - Arquivo existe em: {path} ✅")
                    found = True
                    break
            
            if not found:
                print(f"   - ⚠️  PROBLEMA: Logo path está no banco mas arquivo não existe!")
        else:
            print(f"\n⚠️  EXPLICAÇÃO:")
            print(f"   A marca NIKE não tem logo salvo no banco de dados.")
            print(f"   Por isso a verificação visual não detectou conflito.")
            print(f"   A comparação visual só funciona entre IMAGENS.")
    else:
        print("❌ Marca NIKE não encontrada no banco")
