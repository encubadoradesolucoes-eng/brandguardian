from app import app, db
from sqlalchemy import text

def fix_sequences():
    with app.app_context():
        # Tabelas para as quais queremos sincronizar as sequências
        tables = [
            'alert', 'brand', 'user', 'ipi_record', 'bpi_applicant', 
            'keyword_watch', 'payment', 'entity', 'brand_conflict',
            'process_activity', 'brand_note', 'audit_log'
        ]
        
        print("--- Iniciando Sincronização de Sequências (PostgreSQL) ---")
        
        for table in tables:
            try:
                # Tentar encontrar o nome real da sequência
                result = db.session.execute(text(f"SELECT pg_get_serial_sequence('{table}', 'id')")).fetchone()
                seq_name = result[0] if result and result[0] else f"{table}_id_seq"
                
                # Sincronizar
                db.session.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 1), true)"))
                db.session.commit()
                print(f"✅ Sequência {seq_name} sincronizada com sucesso.")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro na tabela {table}: {e}")
        
        print("--- Sincronização Concluída ---")

if __name__ == "__main__":
    fix_sequences()
