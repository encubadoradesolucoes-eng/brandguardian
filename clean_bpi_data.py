from app import app, db, IpiRecord
from seed_from_deepseek import seed_deepseek

def clean_and_reset():
    print("🧹 Limpando dados BPI reprovados...")
    with app.app_context():
        try:
            # Apaga TUDO da tabela IpiRecord
            num_deleted = db.session.query(IpiRecord).delete()
            db.session.commit()
            print(f"✅ {num_deleted} registros removidos.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao limpar: {e}")
            return

    # Re-importar APENAS o aprovado
    print("🔄 Restaurando apenas dados do Gabarito Oficial...")
    seed_deepseek()

if __name__ == '__main__':
    clean_and_reset()
