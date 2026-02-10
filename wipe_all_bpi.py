from app import app, db, IpiRecord

def wipe_all():
    print("ELIMINANDO TODOS OS DADOS DO BPI (IpiRecord)...")
    with app.app_context():
        try:
            # Apaga tudo sem filtro
            num_deleted = db.session.query(IpiRecord).delete()
            db.session.commit()
            print(f"✅ SUCESSO: {num_deleted} registros foram apagados do banco de dados.")
            print("A tabela IpiRecord está vazia.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO: {e}")

if __name__ == '__main__':
    wipe_all()
