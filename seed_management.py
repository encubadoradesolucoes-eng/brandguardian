from app import app, db, Alert, Brand, User, BrandDocument
from datetime import datetime, timedelta

def seed_management_data():
    with app.app_context():
        print("🌱 Semeando dados de Gestão (Alertas e Documentos)...")
        
        # Pegar usuários para testar
        admin = User.query.filter_by(role='admin').first()
        client = User.query.filter_by(role='client').first()
        
        if not admin or not client:
            print("⚠️ Admin ou Cliente não encontrados. Verifique se o banco tem usuários.")
            return

        # 1. Alertas para o Admin
        alerts = [
            {
                'user_id': admin.id,
                'type': 'CRITICAL',
                'title': 'Oposição Detectada: MYSOLGRID',
                'message': 'Uma nova publicação no BPI 170 conflita diretamente com a marca protegida MYSOLGRID. Prazo legal: 60 dias.'
            },
            {
                'user_id': admin.id,
                'type': 'MEDIUM',
                'title': 'Renovação Pendente: MD Consultores',
                'message': 'A marca MD Consultores entrará em período de renovação em 30 dias. Preparar documentação.'
            },
            {
                'user_id': admin.id,
                'type': 'INFO',
                'title': 'Novo Requerente BPI',
                'message': 'Sistema detectou 15 novos requerentes no setor de Energia em Moçambique.'
            }
        ]
        
        for a_data in alerts:
            alert = Alert(**a_data)
            db.session.add(alert)
            
        # 2. Documentos para uma Marca
        brand = Brand.query.first()
        if brand:
            docs = [
                {
                    'brand_id': brand.id,
                    'title': 'Certificado de Registro #8849',
                    'doc_type': 'certificado',
                    'file_path': '#'
                },
                {
                    'brand_id': brand.id,
                    'title': 'Despacho de Concessão BPI 165',
                    'doc_type': 'despacho',
                    'file_path': '#'
                }
            ]
            for d_data in docs:
                doc = BrandDocument(**d_data)
                db.session.add(doc)
        
        db.session.commit()
        print("✅ Dados de gestão semeados com sucesso!")

if __name__ == '__main__':
    seed_management_data()
