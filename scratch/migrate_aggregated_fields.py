
from app import app, db
from sqlalchemy import text

def migrate_brand_table():
    with app.app_context():
        print("🔍 Verificando e aplicando novas colunas à tabela 'brand'...")
        
        # Lista de novas colunas e seus tipos (Postgres/SQLite compatível)
        new_cols = [
            ("bulletin_number", "VARCHAR(50)"),
            ("filing_date", "VARCHAR(50)"),
            ("publication_date_bpi", "VARCHAR(50)"),
            ("opposition_deadline", "VARCHAR(50)"),
            ("grant_date", "VARCHAR(50)"),
            ("renewal_date", "VARCHAR(50)"),
            ("next_renewal_date", "VARCHAR(50)"),
            ("appeal_deadline", "VARCHAR(50)"),
            ("expiry_date", "VARCHAR(50)"),
            ("next_action", "VARCHAR(200)"),
            ("refusal_reason", "TEXT"),
            ("observations", "TEXT")
        ]
        
        for col_name, col_type in new_cols:
            try:
                # Tenta adicionar a coluna. Se já existir, vai dar erro e nós ignoramos.
                db.session.execute(text(f"ALTER TABLE brand ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"✅ Coluna '{col_name}' adicionada com sucesso.")
            except Exception as e:
                db.session.rollback()
                # O erro 54011 é "duplicate column" no SQLite ou similar no Postgres
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"ℹ️ Coluna '{col_name}' já existe. Ignorado.")
                else:
                    print(f"⚠️ Erro ao adicionar '{col_name}': {e}")

        print("\n🚀 Migração inteligente concluída!")

if __name__ == '__main__':
    migrate_brand_table()
