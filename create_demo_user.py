"""
Script Simplificado - Criar apenas usuário demo
"""

from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

with app.app_context():
    print("🎬 Criando usuário demo...")
    
    # Verificar se já existe
    demo = User.query.filter_by(username='demo').first()
    
    if demo:
        print("⚠️  Usuário demo já existe")
        print(f"   Username: demo")
        print(f"   Plano: {demo.subscription_plan}")
    else:
        # Criar novo
        demo = User(
            username='demo',
            email='demo@m24pro.com',
            name='João Silva',
            password_hash=generate_password_hash('demo123'),
            role='client',
            subscription_plan='professional',
            max_brands=25,
            subscription_start=datetime.utcnow(),
            subscription_end=datetime.utcnow() + timedelta(days=30),
            account_validated=True
        )
        db.session.add(demo)
        db.session.commit()
        
        print("✅ Usuário demo criado com sucesso!")
    
    print("\n📋 CREDENCIAIS:")
    print("   URL: http://localhost:7000")
    print("   Username: demo")
    print("   Password: demo123")
    print("   Plano: Professional")
    print("\n🚀 Pronto para gravar o vídeo!")
