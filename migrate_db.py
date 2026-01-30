from app import app, db, seed_users
import os

def migrate():
    print(">>> Iniciando criação de tabelas e semente de usuários...")
    with app.app_context():
        try:
            db.create_all()
            seed_users() # Garante que o Admin existe no server
            print(">>> Migração concluída com sucesso!")
        except Exception as e:
            print(f">>> Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
