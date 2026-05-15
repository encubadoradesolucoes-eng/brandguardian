from app import app, db
from sqlalchemy import text

def migrate_tr_fields():
    print(">>> Iniciando migração para alinhamento com o TR...")
    with app.app_context():
        # Novos campos para Brand e BpiApplicant
        new_cols = [
            ("brand", "profession", "VARCHAR(150)"),
            ("brand", "brand_type", "VARCHAR(50)"),
            ("brand", "product_description", "TEXT"),
            ("bpi_applicant", "profession", "VARCHAR(150)"),
            ("bpi_applicant", "brand_type", "VARCHAR(50)"),
            ("bpi_applicant", "product_description", "TEXT")
        ]
        
        for table, col, col_type in new_cols:
            try:
                print(f"Adicionando {col} em {table}...")
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                db.session.commit()
                print(f"✅ {col} adicionado com sucesso.")
            except Exception as e:
                db.session.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"ℹ️ {col} já existe em {table}.")
                else:
                    print(f"❌ Erro ao adicionar {col} em {table}: {e}")

    print(">>> Migração TR concluída!")

if __name__ == "__main__":
    migrate_tr_fields()
