from app import app, db
print("🔄 Atualizando banco de dados com nova tabela IpiRecord...")
with app.app_context():
    db.create_all()
    print("✅ Banco de dados atualizado com sucesso!")
