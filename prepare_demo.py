"""
Script de Preparação para Vídeo Demo
Popula o banco de dados com dados realistas para demonstração
"""

from app import app, db, User, Entity, Brand, BrandConflict, RPIMonitoring, SubscriptionPlan
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def prepare_demo_data():
    """Prepara dados realistas para demo"""
    
    with app.app_context():
        print("🎬 Preparando dados para vídeo demo...")
        
        # 1. Criar usuário demo (se não existir)
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            demo_user = User(
                username='demo',
                email='demo@m24pro.com',
                name='João Silva',
                password_hash=generate_password_hash('demo123'),
                role='client',
                subscription_plan='professional',
                max_brands=25,
                subscription_start=datetime.utcnow(),
                subscription_end=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(demo_user)
            print("✅ Usuário demo criado: demo / demo123")
        db.session.commit()
        
        # 2. Criar entidade titular
        demo_entity = Entity.query.filter_by(name='TechCorp Moçambique').first()
        if not demo_entity:
            demo_entity = Entity(
                name='TechCorp Moçambique',
                nuit='400123456',
                email='contato@techcorp.co.mz',
                phone='258840000000',
                address='Av. Julius Nyerere, 1234',
                city='Maputo',
                country='Moçambique'
            )
            db.session.add(demo_entity)
            db.session.commit()
            print("✅ Entidade criada: TechCorp Moçambique")
        
        # 3. Criar marcas de exemplo
        demo_brands = [
            {
                'name': 'TechnoVision',
                'nice_classes': '9, 42',
                'description': 'Software e serviços de tecnologia',
                'status': 'approved',
                'risk_level': 'low',
                'process_number': 'MZ/M/2024/001234'
            },
            {
                'name': 'FreshBite',
                'nice_classes': '30, 43',
                'description': 'Produtos alimentícios e restaurantes',
                'status': 'approved',
                'risk_level': 'low',
                'process_number': 'MZ/M/2024/001235'
            },
            {
                'name': 'UrbanStyle',
                'nice_classes': '25',
                'description': 'Vestuário e acessórios de moda',
                'status': 'under_study',
                'risk_level': 'medium',
                'process_number': 'MZ/M/2024/001236'
            },
            {
                'name': 'EcoClean',
                'nice_classes': '3, 21',
                'description': 'Produtos de limpeza ecológicos',
                'status': 'approved',
                'risk_level': 'low',
                'process_number': 'MZ/M/2024/001237'
            },
            {
                'name': 'SmartHome',
                'nice_classes': '9, 11',
                'description': 'Dispositivos inteligentes para casa',
                'status': 'approved',
                'risk_level': 'low',
                'process_number': 'MZ/M/2024/001238'
            }
        ]
        
        for brand_data in demo_brands:
            existing = Brand.query.filter_by(name=brand_data['name'], user_id=demo_user.id).first()
            if not existing:
                brand = Brand(
                    name=brand_data['name'],
                    nice_classes=brand_data['nice_classes'],
                    description=brand_data['description'],
                    status=brand_data['status'],
                    risk_level=brand_data['risk_level'],
                    process_number=brand_data['process_number'],
                    user_id=demo_user.id,
                    entity_id=demo_entity.id,
                    submission_date=datetime.utcnow() - timedelta(days=random.randint(30, 180))
                )
                db.session.add(brand)
                print(f"✅ Marca criada: {brand_data['name']}")
        
        db.session.commit()
        
        # 4. Criar monitoramento RPI simulado
        rpi = RPIMonitoring.query.filter_by(rpi_number='2024-05').first()
        if not rpi:
            rpi = RPIMonitoring(
                rpi_number='2024-05',
                publication_date=datetime.utcnow() - timedelta(days=7),
                processed=True,
                total_new_marks=156,
                conflicts_detected=2
            )
            db.session.add(rpi)
            print("✅ RPI simulada criada: 2024-05")
        
        db.session.commit()
        
        # 5. Criar conflitos simulados
        techno_brand = Brand.query.filter_by(name='TechnoVision', user_id=demo_user.id).first()
        fresh_brand = Brand.query.filter_by(name='FreshBite', user_id=demo_user.id).first()
        
        conflicts_data = [
            {
                'brand': techno_brand,
                'conflicting_name': 'TechVision',
                'conflicting_number': 'MZ/M/2024/002345',
                'similarity': 85.5,
                'type': 'phonetic'
            },
            {
                'brand': fresh_brand,
                'conflicting_name': 'FreshByte',
                'conflicting_number': 'MZ/M/2024/002346',
                'similarity': 72.3,
                'type': 'moderate'
            }
        ]
        
        for conflict_data in conflicts_data:
            if conflict_data['brand']:
                existing_conflict = BrandConflict.query.filter_by(
                    brand_id=conflict_data['brand'].id,
                    conflicting_mark_number=conflict_data['conflicting_number']
                ).first()
                
                if not existing_conflict:
                    conflict = BrandConflict(
                        brand_id=conflict_data['brand'].id,
                        rpi_id=rpi.id,
                        conflicting_mark_name=conflict_data['conflicting_name'],
                        conflicting_mark_number=conflict_data['conflicting_number'],
                        similarity_score=conflict_data['similarity'],
                        conflict_type=conflict_data['type'],
                        status='pending',
                        notified=True,
                        created_at=datetime.utcnow() - timedelta(days=3)
                    )
                    db.session.add(conflict)
                    print(f"✅ Conflito criado: {conflict_data['brand'].name} vs {conflict_data['conflicting_name']}")
        
        db.session.commit()
        
        print("\n🎉 Dados de demo preparados com sucesso!")
        print("\n📋 CREDENCIAIS PARA DEMO:")
        print("   Username: demo")
        print("   Password: demo123")
        print("\n📊 DADOS CRIADOS:")
        print(f"   • 1 Usuário (Professional)")
        print(f"   • 1 Entidade (TechCorp)")
        print(f"   • {len(demo_brands)} Marcas")
        print(f"   • 2 Conflitos detectados")
        print(f"   • 1 RPI processada")
        print("\n🚀 Pronto para gravar o vídeo!")

if __name__ == '__main__':
    prepare_demo_data()
