import csv
import os
from datetime import datetime
from app import app, db, IpiRecord

def seed_csvs():
    base_dir = os.path.join(app.root_path, 'bpi')
    req_file = os.path.join(base_dir, 'requerentes_bpi_junho_2023.csv')
    con_file = os.path.join(base_dir, 'concessoes_bpi_junho_2023.csv')

    print(f"📂 Lendo CSVs de: {base_dir}")

    # 1. Carregar Requerentes em Memória
    applicants = {}
    try:
        with open(req_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                applicants[row['req_id']] = row['req_nome']
        print(f"✅ {len(applicants)} requerentes carregados.")
    except Exception as e:
        print(f"❌ Erro ao ler requerentes: {e}")
        return

    # 2. Inserir Concessões
    count = 0
    with app.app_context():
        # Limpar antes (opcional, já fizemos wipe)
        try:
            with open(con_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse Data
                    data_pub = None
                    if row['data_concessao']:
                        try:
                            data_pub = datetime.strptime(row['data_concessao'], '%d/%m/%Y').date()
                        except:
                            pass # Data inválida ou vazia, deixa None

                    # Nome da Marca (tratar [sem nome] se houver)
                    brand_name = row['marca']
                    if brand_name == '[sem nome]':
                        brand_name = "Marca Figurativa (Sem Nome)"

                    rec = IpiRecord(
                        process_number=row['proc_id'],
                        record_type='marca',
                        status='concessao', # CSV é de concessões
                        brand_name=brand_name[:250],
                        applicant_name=applicants.get(row['req_id'], 'Desconhecido')[:250],
                        nice_class=row['classe'],
                        publication_date=data_pub,
                        bulletin_number='BPI-170'  # Fonte Explicita
                    )
                    db.session.add(rec)
                    count += 1
            
            db.session.commit()
            print(f"✅ SUCESSO: {count} registros de concessão importados do CSV.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na importação: {e}")

if __name__ == '__main__':
    seed_csvs()
