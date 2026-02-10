import csv
import os
from datetime import datetime
from app import app, db, IpiRecord

def import_correct_data():
    print("🚀 Iniciando importação dos DADOS OFICIAIS CORRETOS...")
    
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    conc_file = os.path.join(base_dir, "concessoes_bpi_junho_2023.csv")
    req_file = os.path.join(base_dir, "requerentes_bpi_junho_2023.csv")
    
    # 1. Limpar tabela anterior
    with app.app_context():
        print("🧹 Limpando registros antigos...")
        db.session.query(IpiRecord).delete()
        db.session.commit()
    
    # 2. Carregar Requerentes (Dicionário)
    requerentes = {}
    print(f"📖 Lendo Requerentes: {req_file}")
    try:
        with open(req_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # req_id,req_nome,...
                rid = row.get('req_id')
                nome = row.get('req_nome')
                if rid and nome:
                    requerentes[rid] = nome
        print(f"✅ {len(requerentes)} requerentes carregados.")
    except Exception as e:
        print(f"❌ Erro lendo requerentes: {e}")
        return

    # 3. Importar Concessões
    print(f"📖 Lendo Concessões e Cruzando: {conc_file}")
    count = 0
    with app.app_context():
        try:
            with open(conc_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # proc_id,marca,classe,data_concessao,ano,boletim,req_id
                
                for row in reader:
                    proc = row.get('proc_id')
                    marca = row.get('marca')
                    classe = row.get('classe')
                    req_id = row.get('req_id')
                    boletim = row.get('boletim')
                    
                    # Cruzamento
                    titular = requerentes.get(req_id, f"Desconhecido ({req_id})")
                    
                    # Data (tratar falhas)
                    data_str = row.get('data_concessao')
                    pub_date = None
                    if data_str:
                        try:
                            pub_date = datetime.strptime(data_str, '%d/%m/%Y').date()
                        except:
                            pass # Ignora data inválida
                    
                    if not pub_date:
                        # Fallback
                        pub_date = datetime(2023, 6, 1).date()

                    rec = IpiRecord(
                        process_number=proc,
                        brand_name=marca,
                        nice_class=classe,
                        applicant_name=titular,
                        bulletin_number=boletim,
                        record_type='marca',
                        status='concessao',
                        publication_date=pub_date,
                        imported_at=datetime.utcnow()
                    )
                    db.session.add(rec)
                    count += 1
            
            db.session.commit()
            print(f"✅ SUCESSO! {count} registros oficiais importados.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na importação: {e}")

if __name__ == '__main__':
    import_correct_data()
