from app import app, db, IpiRecord
from datetime import datetime

# Dados fornecidos pelo DeepSeek (Gabarito Oficial)
data_deepseek = {
    'pedidos': [
        {'process': '47471/2023', 'brand': '29', 'class': '29', 'applicant': 'ZHIZHA, LIMITADA', 'date': '15/06/2023'},
        {'process': '47520/2023', 'brand': 'SHOCOLATA', 'class': '16', 'applicant': 'RIM TRADING E INDUSTRIA, LDA', 'date': '15/06/2023'},
        {'process': '47649/2023', 'brand': 'ANIGO', 'class': '35', 'applicant': 'CASA BAKALI, EI', 'date': '15/06/2023'},
        {'process': '47761/2023', 'brand': 'GOFUEL', 'class': '36', 'applicant': 'DUMBA MICROBANCO, SA', 'date': '15/06/2023'}
    ],
    'renovacoes': [
        {'process': '6116/2002', 'brand': 'Form-Scaff', 'class': '37', 'applicant': 'Waco Africa (Proprietary) Limited'},
        {'process': '6487/2002', 'brand': 'Mazoe', 'class': '32', 'applicant': 'Atlantic Industries'},
        {'process': '6930/2003', 'brand': 'Safari', 'class': '34', 'applicant': 'British American Tobacco (Brands) Limited'},
        {'process': '6989/2003', 'brand': 'Maille', 'class': '29', 'applicant': 'Unilever Ip Holdings B.V.'},
        {'process': '7025/2003', 'brand': 'Hellmann\'s', 'class': '30', 'applicant': 'Conopco Inc.'}
    ],
    'recusas': [
        {'process': '47238/2023', 'brand': 'Fig.', 'class': '37', 'applicant': 'Stefanutti Stocks Holdings Limited', 'status': 'recusa_provisoria'},
        {'process': '47239/2023', 'brand': 'Stefanutti Stocks', 'class': '37', 'applicant': 'Stefanutti Stocks Holdings Limited', 'status': 'recusa_provisoria'},
        {'process': '46162/2023', 'brand': 'Thompson', 'class': '43', 'applicant': 'GEN4 Foods (Pty) Ltd.', 'status': 'recusa_definitiva'},
        {'process': '47263/2023', 'brand': 'Elite', 'class': '32', 'applicant': 'Engie Energy Access Mocambique, Lda', 'status': 'recusa_definitiva'}
    ],
    'caducidade': [
        {'process': '22103/2012', 'brand': 'Wi-Fi Tvcabo', 'class': '38', 'applicant': 'TVcabo Comunicacoes Multimedia, Limitada'},
        {'process': '22108/2012', 'brand': 'Gemubleyd', 'class': '13', 'applicant': 'Fabrica de Explosivos (moc.), Lda'},
        {'process': '22110/2012', 'brand': 'Domus', 'class': '36', 'applicant': 'Domus - Sociedade de Gestao Imobiliaria'}
    ]
}

def seed_deepseek():
    print("🚀 Adicionando dados complementares (DeepSeek Gabarito)...")
    with app.app_context():
        # (Lógica de wipe removida para não apagar CSVs)
        count = 0
        
        # Data padrão se não fornecida (2023-06-15 do Boletim 170)
        default_date = datetime(2023, 6, 15).date()
        
        # 1. Pedidos
        for item in data_deepseek['pedidos']:
            rec = IpiRecord(
                process_number=item['process'],
                record_type='marca',
                status='pedido',
                brand_name=item['brand'],
                applicant_name=item['applicant'],
                nice_class=item['class'],
                publication_date=default_date,
                bulletin_number='BPI-170'
            )
            db.session.add(rec)
            count += 1

        # 2. Renovações
        for item in data_deepseek['renovacoes']:
            rec = IpiRecord(
                process_number=item['process'],
                record_type='marca',
                status='renovacao',
                brand_name=item['brand'],
                applicant_name=item['applicant'],
                nice_class=item['class'],
                publication_date=default_date,
                bulletin_number='BPI-170'
            )
            db.session.add(rec)
            count += 1
                
        # 3. Recusas
        for item in data_deepseek['recusas']:
            rec = IpiRecord(
                process_number=item['process'],
                record_type='marca',
                status=item.get('status', 'recusa'),
                brand_name=item['brand'],
                applicant_name=item['applicant'],
                nice_class=item['class'],
                publication_date=default_date,
                bulletin_number='BPI-170'
            )
            db.session.add(rec)
            count += 1
                
        # 4. Caducidade
        for item in data_deepseek['caducidade']:
            rec = IpiRecord(
                process_number=item['process'],
                record_type='marca',
                status='caducidade',
                brand_name=item['brand'],
                applicant_name=item['applicant'],
                nice_class=item['class'],
                publication_date=default_date,
                bulletin_number='BPI-170'
            )
            db.session.add(rec)
            count += 1
        
        try:
            db.session.commit()
            print(f"✅ Sucesso! {count} novos registros OFICIAIS (Gabarito DeepSeek) adicionados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar: {e}")

if __name__ == '__main__':
    seed_deepseek()
