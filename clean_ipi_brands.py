from app import app, db, IpiRecord

def clean_only_brands():
    print("🧹 Iniciando limpeza cirúrgica das MARCAS IPI (mantendo Logótipos)...")
    with app.app_context():
        # Deletar apenas marcas de concessão (tabela)
        deleted = IpiRecord.query.filter_by(record_type='marca', status='concessao').delete()
        db.session.commit()
        print(f"✅ {deleted} marcas removidas. Logótipos preservados.")

if __name__ == '__main__':
    clean_only_brands()
