from app import app, db, seed_users
import os

# Garante que a pasta existe
if not os.path.exists('instance'):
    os.makedirs('instance')

# Executa a recriação
with app.app_context():
    print("1. Criando tabelas...")
    db.create_all()
    
    print("2. Criando usuário Admin...")
    seed_users()
    
    print("✅ PRONTO. Tente logar agora.")
