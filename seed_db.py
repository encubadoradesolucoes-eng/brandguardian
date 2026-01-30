from app import app, db, Brand, Entity
from datetime import datetime, timedelta
import random

def seed_database():
    print(">>> Iniciando populacao do banco de dados M24...")
    
    with app.app_context():
        # Limpar tabelas existentes
        print(">>> Limpando dados antigos...")
        try:
            db.session.query(Brand).delete()
            db.session.query(Entity).delete()
            db.session.commit()
        except Exception as e:
            print(f"Erro ao limpar (pode ser normal se tabelas vazias): {e}")

        # 1. Criar Titulares (Entities)
        owners = []
        owner_data = [
            ("Coca-Cola Company", True), ("Nike Inc.", True), ("Apple Inc.", True), 
            ("Samsung Electronics", True), ("Toyota Motor Corp", True), 
            ("M24 Solutions", True), ("Grupo Entreposto", True), 
            ("Banco de Moçambique", False), ("MCEL - Moçambique Celular", True), 
            ("Vodacom Moçambique", True)
        ]
        
        for name, is_corp in owner_data:
            # Campos do Model: name, nuit, email, phone, website, address, city, country
            owner = Entity(
                name=name,
                nuit=str(random.randint(100000000, 999999999)),
                email=f"contact@{name.lower().replace(' ', '').replace('.', '')}.com",
                phone=f"+258 84 {random.randint(1000000, 9999999)}",
                address="Maputo, Moçambique",
                city="Maputo",
                country="MZ"
            )
            owners.append(owner)
            db.session.add(owner)
        
        db.session.commit() # Salvar para ter IDs se precisasse, mas Brand não usa FK
        print(f">>> {len(owners)} Titulares criados.")

        # 2. Criar Marcas (Brands)
        # Campos Model Brand: property_type, name, registration_number, nice_classes, country, status...
        # owner_name, owner_email, owner_nuit...
        
        brand_names = [
            # Globais
            "Coca-Cola", "Fanta", "Sprite", "Nike Air", "Just Do It", "Iphone", "Galaxy S", 
            "Corolla", "Hilux", "PlayStation", "Windows", "Office 365", "Google Search",
            # Locais / Fictícias
            "M24 Brand Guardian", "2M Cervejas", "Laurentina", "Água de Namaacha", 
            "Topack Embalagens", "Mimmos Pizza", "Shoprite MZ", "Clube Naval",
            "BIM Net", "Standard Bank App", "Millennium IZI", "E-Mola", "M-Pesa",
            "Global Alliance Seguros", "Hollard", "Compal", "Sumol", "Delta Cafés",
            "Nando's", "Ocean Basket", "Spur Steak Ranches", "Debonairs Pizza",
            "TV Miramar", "STV Notícias", "Jornal Notícias", "O País",
            "Tudobom Supermercados", "Premier Grupo", "Cimentos de Moçambique",
            "Mozal Aluminium", "Vale Moçambique", "Total Energies", "Galp Energia",
            "Petromoc", "Electricidade de Moçambique", "FIPAG", "Águas da Região de Maputo"
        ]

        # Status distribution weights
        statuses = ['registered', 'pending', 'rejected', 'expired']
        weights = [0.6, 0.3, 0.05, 0.05] # 60% registradas
        
        risks = ['low', 'medium', 'high']
        risk_weights = [0.7, 0.2, 0.1] # 10% alto risco

        count = 0
        for b_name in brand_names:
            owner = random.choice(owners)
            status = random.choices(statuses, weights)[0]
            risk = random.choices(risks, risk_weights)[0]
            
            reg_date = datetime.now() - timedelta(days=random.randint(100, 3000))
            
            # ATENÇÃO: Campos devem bater exatamente com Brand(db.Model)
            brand = Brand(
                name=b_name,
                property_type="marca",
                # owner_id removido pois não existe no model
                owner_name=owner.name,
                owner_email=owner.email,
                owner_nuit=owner.nuit,
                
                nice_classes=f"{random.randint(1, 45)}, {random.randint(1, 45)}",
                status=status,
                registration_number=f"MZ/{datetime.now().year}/{random.randint(1000, 9999)}",
                # deposit_date não existe no model? Verificando... submission_date existe.
                submission_date=reg_date,
                country="MZ",
                
                logo_path=None, 
                risk_level=risk,
                risk_score=float(random.randint(70, 99) if risk == 'high' else random.randint(0, 69))
            )
            db.session.add(brand)
            count += 1

        db.session.commit()
        print(f">>> {count} Marcas criadas com sucesso.")
        print(">>> BANCO DE DADOS POPULADO! REINICIE O SERVIDOR.")

if __name__ == '__main__':
    seed_database()
