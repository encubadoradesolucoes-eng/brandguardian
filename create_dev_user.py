from app import app, db, User
from werkzeug.security import generate_password_hash

def create_dev():
    with app.app_context():
        # Verifica se o usuário já existe
        dev = User.query.filter_by(email='developer@incubadora.com').first()
        if not dev:
            dev = User(
                name='M24 Developer',
                email='developer@incubadora.com',
                password=generate_password_hash('pandorabox5229'),
                role='admin' # Role admin para ter acesso base, mas as rotas dev são bloqueadas por email
            )
            db.session.add(dev)
            db.session.commit()
            print(">>> Usuário Developer criado com sucesso!")
            print(">>> Login: developer@incubadora.com")
            print(">>> Pass: pandorabox5229")
        else:
            print(">>> Usuário Developer já existe.")

if __name__ == "__main__":
    create_dev()
