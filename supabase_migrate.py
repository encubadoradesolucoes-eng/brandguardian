import os
import sys

# Adiciona o diretório atual ao sys.path para garantir que os módulos locais sejam importados
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import make_transient
from app import app, db
# Import all models to ensure they are registered
from app import (
    User, EmailLog, SubscriptionPlan, RPIMonitoring, NiceClass, 
    BrandConflict, Payment, Entity, Brand, IpiRecord, BpiApplicant, 
    BrandLog, Alert, AuditLog, Task, BrandDocument
)

# Source SQLite
sqlite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'brands.db')
sqlite_uri = 'sqlite:///' + sqlite_path

# Destination Postgres
postgres_uri = "postgresql://postgres:pandorabox5229@db.austbyfpjimfjrtuvujx.supabase.co:5432/postgres"

def migrate_data():
    print(f"🚀 Iniciando migração de {sqlite_uri} para Supabase...")
    
    # 1. Create tables in Postgres
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
    with app.app_context():
        print("Criando tabelas no Supabase...")
        db.create_all()
        print("✅ Tabelas criadas.")

    # 2. Extract data from SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
    
    models = [
        User, SubscriptionPlan, NiceClass, Entity, Brand, 
        EmailLog, RPIMonitoring, BrandConflict, Payment, 
        IpiRecord, BpiApplicant, BrandLog, Alert, AuditLog, 
        Task, BrandDocument
    ]
    
    table_data = {}
    with app.app_context():
        for model in models:
            try:
                records = model.query.all()
                table_data[model] = records
                print(f"📦 Extraído {len(records)} registros de {model.__name__}")
            except Exception as e:
                print(f"⚠️ Erro ao ler {model.__name__}: {e}")

    # 3. Insert into Postgres
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
    with app.app_context():
        for model in models:
            records = table_data.get(model, [])
            if not records:
                continue
            
            print(f"📤 Inserindo {len(records)} registros em {model.__name__}...")
            # Iniciar uma nova sessão para inserção
            for record in records:
                db.session.expunge(record)
                make_transient(record)
                db.session.add(record)
            
            try:
                db.session.commit()
                print(f"✅ {model.__name__} migrado.")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao inserir {model.__name__}: {e}")

if __name__ == "__main__":
    migrate_data()
