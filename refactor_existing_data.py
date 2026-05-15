from app import app, db, Brand, BpiApplicant, BrandLog
from modules.normalizer import normalize_name, normalize_status, normalize_date
from modules.constants import BrandStatus
from sqlalchemy import text

def cleanup_and_normalize():
    print("🚀 Iniciando limpeza e normalização de dados (TR Alignment)...")
    
    with app.app_context():
        # 1. Normalizar BRANDS
        brands = Brand.query.all()
        print(f"📦 Processando {len(brands)} marcas...")
        for b in brands:
            b.name = normalize_name(b.name)
            b.owner_name = normalize_name(b.owner_name)
            b.status = normalize_status(b.status)
            b.filing_date = normalize_date(b.filing_date)
            
            # Limpeza de campos simulados se necessário
            if b.registered_by == 'Sistema m24' and not b.process_number:
                 # Exemplo de remoção de lixo
                 pass

        # 2. Normalizar BPI_APPLICANTS
        applicants = BpiApplicant.query.all()
        print(f"👥 Processando {len(applicants)} requerentes...")
        for a in applicants:
            a.name = normalize_name(a.name)
            a.brand_name = normalize_name(a.brand_name)
            a.status = normalize_status(a.status) # Converte STATUS_01 etc para NOMES REAIS
            a.filing_date = normalize_date(a.filing_date)

        # 3. Normalizar LOGS
        logs = BrandLog.query.all()
        for l in logs:
            l.action_type = l.action_type.upper()

        try:
            db.session.commit()
            print("✅ Normalização concluída com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar normalização: {e}")

        # 4. EXCLUIR O QUE ESTÁ A MAIS (Opcional: Marcas sem número de processo ou duplicadas)
        # Por enquanto, vamos apenas remover marcas com nomes de teste óbvios
        test_terms = ['teste', 'test', 'demo', 'asdf', '123']
        deleted_count = 0
        for b in Brand.query.all():
            if any(term in b.name.lower() for term in test_terms):
                db.session.delete(b)
                deleted_count += 1
        
        db.session.commit()
        print(f"🗑️ Removidas {deleted_count} marcas de teste/lixo.")

if __name__ == "__main__":
    cleanup_and_normalize()
