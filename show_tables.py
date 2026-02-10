"""
Lista todas as tabelas verificadas pelo sistema
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from sqlalchemy import inspect

with app.app_context():
    print("=" * 70)
    print("TABELAS DO BANCO DE DADOS")
    print("=" * 70)
    
    # Pega o inspetor do banco
    inspector = inspect(db.engine)
    
    # Lista todas as tabelas
    tabelas = inspector.get_table_names()
    
    print(f"\n📊 Total de tabelas: {len(tabelas)}")
    print()
    
    for i, tabela in enumerate(tabelas, 1):
        print(f"{i}. {tabela}")
        
        # Pega colunas da tabela
        colunas = inspector.get_columns(tabela)
        print(f"   Colunas ({len(colunas)}):")
        for col in colunas[:5]:  # Mostra primeiras 5
            print(f"      - {col['name']} ({col['type']})")
        if len(colunas) > 5:
            print(f"      ... e mais {len(colunas) - 5} colunas")
        
        # Tenta contar registros
        try:
            from sqlalchemy import text
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
            count = result.scalar()
            print(f"   📈 Registros: {count}")
        except:
            print(f"   📈 Registros: (erro ao contar)")
        
        print()
    
    print("=" * 70)
    print("TABELAS VERIFICADAS NA VARREDURA")
    print("=" * 70)
    print()
    
    print("1️⃣  IpiRecord (Registro BPI)")
    print("   - Contém: Marcas registradas no BPI de Moçambique")
    print("   - Campos principais:")
    print("      • brand_name: Nome da marca")
    print("      • process_number: Número do processo")
    print("      • applicant_name: Nome do requerente/titular")
    print("      • nice_class: Classe de Nice")
    print("      • status: Status do registro")
    print("      • publication_date: Data de publicação")
    print("      • image_path: Caminho da imagem (para verificação visual)")
    
    from app import IpiRecord
    total_ipi = IpiRecord.query.count()
    com_imagem = IpiRecord.query.filter(IpiRecord.image_path.isnot(None)).count()
    print(f"   📊 Total: {total_ipi} registros")
    print(f"   🖼️  Com imagem: {com_imagem} registros")
    print()
    
    print("2️⃣  Brand (Marcas de Usuários)")
    print("   - Contém: Marcas cadastradas pelos usuários do sistema")
    print("   - Campos principais:")
    print("      • name: Nome da marca")
    print("      • owner_name: Nome do titular")
    print("      • nice_classes: Classes de Nice")
    print("      • logo_path: Caminho do logo")
    print("      • user_id: Usuário que cadastrou")
    
    from app import Brand
    total_brands = Brand.query.count()
    com_logo = Brand.query.filter(Brand.logo_path.isnot(None)).count()
    print(f"   📊 Total: {total_brands} marcas")
    print(f"   🖼️  Com logo: {com_logo} marcas")
    print()
    
    print("=" * 70)
    print("VERIFICAÇÕES QUE USAM CADA TABELA")
    print("=" * 70)
    print()
    
    print("🔍 SCAN TEXTUAL (scan_live_real)")
    print("   └─ IpiRecord: Busca similaridade textual/fonética")
    print("      • Usa: brand_name, process_number, nice_class, status")
    print()
    
    print("🖼️  VERIFICAÇÃO VISUAL (verificacao_imagem_real)")
    print("   ├─ Brand: Compara com logos de usuários")
    print("   │  • Usa: logo_path, name, owner_name")
    print("   └─ IpiRecord: Compara com imagens do BPI")
    print("      • Usa: image_path, brand_name, process_number")
    print()
    
    print("🧹 PURIFICATION (purification_real)")
    print("   └─ Brand: Audita qualidade dos dados de marcas")
    print("      • Analisa todos os campos para inconsistências")
    print()
    
    print("=" * 70)
