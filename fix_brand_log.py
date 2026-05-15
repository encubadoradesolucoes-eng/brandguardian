from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Adicionar coluna user_id à tabela brand_log
        db.session.execute(text("ALTER TABLE brand_log ADD COLUMN user_id INTEGER REFERENCES \"user\"(id);"))
        db.session.commit()
        print("Coluna user_id adicionada com sucesso à tabela brand_log!")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")
        db.session.rollback()
        
        # Se o erro for que já existe, tudo bem
        if "already exists" in str(e):
            print("A coluna já existe. Continuando...")
        else:
            raise e
