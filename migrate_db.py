from app import app, db
import os

def migrate():
    print(">>> Iniciando criação de tabelas no PostgreSQL/SQLite...")
    with app.app_context():
        try:
            db.create_all()
            print(">>> Tabelas criadas com sucesso!")
        except Exception as e:
            print(f">>> Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
