from app import app, db, BpiApplicant

with app.app_context():
    print("🗑️ Renovando estrutura do banco para incluir Perfil Mestre...")
    BpiApplicant.__table__.drop(db.engine, checkfirst=True)
    db.create_all()
    print("✅ Banco pronto para todos os dados (Processes + Master Profiles)!")
