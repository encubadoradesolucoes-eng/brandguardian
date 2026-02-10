from app import app, db
from sqlalchemy import text

def force_migrate():
    with app.app_context():
        print(f"Usando DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
        engine = db.engine
        
        columns = [
            ("last_active", "DATETIME"),
            ("agent_registration_number", "VARCHAR(50)"),
            ("agent_bio", "TEXT"),
            ("subscription_plan", "VARCHAR(50)"),
            ("subscription_start", "DATETIME"),
            ("subscription_end", "DATETIME"),
            ("max_brands", "INTEGER")
        ]
        
        with engine.connect() as conn:
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Coluna '{col_name}' adicionada via SQLAlchemy Engine.")
                except Exception as e:
                    print(f"ℹ️ Coluna '{col_name}' provavelmente já existe ou erro: {str(e)[:50]}")
            conn.commit()
        print("🚀 Migração forçada concluída!")

if __name__ == '__main__':
    force_migrate()
