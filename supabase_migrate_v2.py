import os
import sys
from sqlalchemy import create_engine, MetaData, Table, select, insert

# Destination Postgres
postgres_uri = "postgresql://postgres:pandorabox5229@db.austbyfpjimfjrtuvujx.supabase.co:5432/postgres"
# Source SQLite
sqlite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'brands.db')
sqlite_uri = 'sqlite:///' + sqlite_path

def migrate_data():
    print(f"🚀 Iniciando migração v2...")
    
    # Engines
    src_engine = create_engine(sqlite_uri)
    dest_engine = create_engine(postgres_uri)
    
    src_meta = MetaData()
    src_meta.reflect(bind=src_engine)
    
    # Get table names in order (careful with FKs if possible, or just disable triggers)
    # Tables in order based on dependencies found in app.py (User first, then others)
    # To simplify, we can ignore FKs for a moment if we are careful or just copy all.
    
    tables_to_migrate = [
        'user', 'subscription_plan', 'nice_class', 'entity', 'brand', 
        'email_log', 'rpi_monitoring', 'brand_conflict', 'payment', 
        'ipi_record', 'bpi_applicant', 'brand_log', 'alert', 'audit_log', 
        'task', 'brand_document'
    ]
    
    with dest_engine.connect() as dest_conn:
        print("💡 Dica: Se houver erros de Foreign Key, desative os triggers temporariamente no console do Supabase.")
        
        for table_name in tables_to_migrate:
            if table_name not in src_meta.tables:
                print(f"❓ Tabela {table_name} não encontrada no SQLite. Pulando.")
                continue
                
            print(f"📦 Migrando tabela: {table_name}...")
            src_table = src_meta.tables[table_name]
            
            # Read data
            with src_engine.connect() as src_conn:
                rows = src_conn.execute(select(src_table)).fetchall()
                data = [dict(row._mapping) for row in rows]
            
            if not data:
                print(f"   (Vazia)")
                continue
            
            # Clean data (SQLite booleans might be 1/0, but Postgres likes True/False)
            # SQLAlchemy usually handles this if types match.
            
            # Insert data
            dest_table = Table(table_name, MetaData(), autoload_with=dest_engine)
            
            try:
                # Truncate first to be safe (optional)
                # dest_conn.execute(dest_table.delete())
                
                # Batch insert
                dest_conn.execute(insert(dest_table), data)
                dest_conn.commit()
                print(f"✅ Migrados {len(data)} registros para {table_name}.")
            except Exception as e:
                print(f"❌ Erro em {table_name}: {e}")
                dest_conn.rollback()

if __name__ == "__main__":
    migrate_data()
