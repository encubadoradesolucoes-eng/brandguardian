import csv
import os
from datetime import datetime
from app import app, db, IpiRecord

def import_analyzed_data():
    print("🚀 Iniciando importação cruzada de dados analisados...")
    
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    req_file = os.path.join(base_dir, "m24_analyzer_requerentes_BPI-170-Junho.csv")
    conc_file = os.path.join(base_dir, "m24_analyzer_concessoes_BPI-170-Junho.csv")
    
    # 1. Carregar Requerentes em Memória
    requerentes = {}
    print(f"Lendo requerentes de: {req_file}")
    try:
        with open(req_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV headers: ID_Requerente,Nome_Requerente,Pagina_Detectado
                rid = row.get('ID_Requerente')
                nome = row.get('Nome_Requerente')
                if rid and nome:
                    requerentes[rid] = nome
        print(f"✅ {len(requerentes)} requerentes carregados.")
    except Exception as e:
        print(f"❌ Erro ao ler requerentes: {e}")
        return

    # 2. Carregar Concessões e Cruzar
    print(f"Lendo concessões de: {conc_file}")
    count = 0
    with app.app_context():
        try:
            with open(conc_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # CSV headers: Processo,Marca,Classe,ID_Requerente,Pagina_BPI
                
                for row in reader:
                    proc = row.get('Processo')
                    marca = row.get('Marca')
                    classe = row.get('Classe')
                    rid = row.get('ID_Requerente')
                    
                    # Cruzamento
                    titular = requerentes.get(rid, "Desconhecido")
                    
                    # Evitar duplicatas (Opcional, mas bom)
                    existing = IpiRecord.query.filter_by(process_number=proc).first()
                    if existing:
                        # Atualizar dados se necessário
                        existing.applicant_name = titular
                        existing.brand_name = marca
                    else:
                        rec = IpiRecord(
                            process_number=proc,
                            brand_name=marca,
                            nice_class=classe,
                            applicant_name=titular,
                            bulletin_number='BPI-170',
                            record_type='marca',
                            status='concessao', # Assumindo concessão pois veio da lista de concessões
                            publication_date=datetime(2023, 6, 15).date(),
                            imported_at=datetime.utcnow()
                        )
                        db.session.add(rec)
                    
                    count += 1
                    if count % 100 == 0:
                        print(f"Processando... {count}")
            
            db.session.commit()
            print(f"✅ Importação Concluída! {count} marcas processadas/atualizadas com sucesso.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na importação: {e}")

if __name__ == '__main__':
    import_analyzed_data()
