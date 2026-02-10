from app import app, db
from sqlalchemy import text, inspect
import os

def repair_db():
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        
        # Mapeamento de Tabelas -> Novos Campos (além do que o create_all criaria se a tabela estivesse vazia)
        # Como estamos evoluindo o esquema, precisamos adicionar colunas novas manualmente em tabelas existentes
        
        schema_tweaks = {
            'user': [
                ("last_active", "DATETIME"),
                ("agent_registration_number", "VARCHAR(50)"),
                ("agent_bio", "TEXT"),
                ("subscription_plan", "VARCHAR(50)"),
                ("subscription_start", "DATETIME"),
                ("subscription_end", "DATETIME"),
                ("max_brands", "INTEGER")
            ],
            'brand': [
                ("agent_id", "INTEGER"),
                ("registration_mode", "VARCHAR(50)"),
                ("registered_by", "VARCHAR(100)"),
                ("phonetic_score", "FLOAT"),
                ("visual_score", "FLOAT")
            ],
            'bpi_applicant': [
                # Muitos campos foram adicionados recentemente
                ("brand_name", "VARCHAR(200)"),
                ("filing_date", "VARCHAR(50)"),
                ("publication_date_bpi", "VARCHAR(50)"),
                ("nice_class", "VARCHAR(50)"),
                ("observations", "TEXT"),
                ("next_action", "VARCHAR(200)"),
                ("deadline", "VARCHAR(50)"),
                ("alteration_type", "VARCHAR(100)"),
                ("alteration_details", "TEXT"),
                ("opposition_deadline", "VARCHAR(50)"),
                ("renewal_date", "VARCHAR(50)"),
                ("next_renewal_date", "VARCHAR(50)"),
                ("appeal_deadline", "VARCHAR(50)"),
                ("refusal_reason", "TEXT"),
                ("renunciation_date", "VARCHAR(50)"),
                ("final_refusal_date", "VARCHAR(50)"),
                ("expiry_date", "VARCHAR(50)"),
                ("renewal_deadline", "VARCHAR(50)"),
                ("triple_fee", "VARCHAR(20)"),
                ("definite_expiry_date", "VARCHAR(50)"),
                ("grant_date", "VARCHAR(50)"),
                ("nationality", "VARCHAR(100)"),
                ("full_address", "TEXT"),
                ("total_processes", "INTEGER")
            ]
        }
        
        print("🔍 Iniciando Inspeção Profunda do Banco de Dados...")
        
        with engine.connect() as conn:
            for table_name, columns in schema_tweaks.items():
                if not inspector.has_table(table_name):
                    print(f"⚠️ Tabela '{table_name}' não existe. Ignorando tweaks.")
                    continue
                
                existing_cols = [c['name'] for c in inspector.get_columns(table_name)]
                
                for col_name, col_type in columns:
                    if col_name not in existing_cols:
                        try:
                            # Sqlite ALTER TABLE
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                            print(f"✅ [{table_name}] Coluna '{col_name}' adicionada.")
                        except Exception as e:
                            print(f"❌ [{table_name}] Erro ao adicionar '{col_name}': {e}")
                    else:
                        # print(f"ℹ️ [{table_name}] '{col_name}' já existe.")
                        pass
            
            conn.commit()
            
        # Garantir que todas as tabelas novas existam
        db.create_all()
        print("🚀 Banco de Dados Sincronizado com os Modelos Atuais!")

if __name__ == '__main__':
    repair_db()
