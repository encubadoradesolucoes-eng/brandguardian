from app import app, db, User
with app.app_context():
    try:
        u = User.query.first()
        print(f"Sucesso ao ler admin_registration_number: {u.agent_registration_number if u else 'Sem users'}")
    except Exception as e:
        print(f"ERRO AO LER USER: {e}")
