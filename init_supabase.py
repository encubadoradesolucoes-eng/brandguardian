import os
from app import app, db
import app as main_app # to access models

postgres_uri = "postgresql://postgres:pandorabox5229@db.austbyfpjimfjrtuvujx.supabase.co:5432/postgres"

def init_supabase():
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
    with app.app_context():
        print("🛠️ Criando tabelas no Supabase...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso.")

if __name__ == "__main__":
    init_supabase()
