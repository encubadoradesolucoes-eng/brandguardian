import csv
import os
import secrets
from app import app, db, BpiApplicant

def get_status_from_page(page_str):
    """Mapeamento solicitado pelo usuário baseado nas páginas do Boletim"""
    try:
        page = int(page_str)
        if 9 <= page <= 44: return 'STATUS_01'  # PUBLICADO
        if page == 45: return 'STATUS_02'       # CONCEDIDO
        if 46 <= page <= 48: return 'STATUS_03' # RENOVADO
        if page == 49: return 'STATUS_04'       # RECUSA_PROVISORIA
        if page == 50: return 'STATUS_06'       # RECUSA_DEFINITIVA
        if 51 <= page <= 63: return 'STATUS_07' # AVISO_CADUCIDADE
        if 64 <= page <= 74: return 'STATUS_08' # CADUCO_DEFINITIVO
        if 75 <= page <= 91: return 'STATUS_09' # ALTERADO
        return 'new'
    except:
        return 'new'

def import_applicants():
    print("🚀 Iniciando importação de Requerentes (Leads BPI)...")
    
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    # Tenta usar o arquivo mais completo se existir, senão usa o padrão
    req_file = os.path.join(base_dir, "m24_analyzer_requerentes_BPI-170-Junho.csv")
    if not os.path.exists(req_file):
        req_file = os.path.join(base_dir, "requerentes_bpi_junho_2023.csv")
    
    with app.app_context():
        # 1. Garantir que tabela existe com a nova estrutura (incluindo campo 'page')
        print("🛠️ Aplicando nova estrutura de banco de dados...")
        try:
            db.create_all()
        except:
            pass
            
        print(f"📖 Lendo arquivo: {req_file}")
        count = 0
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Tenta capturar a página do CSV se existir
                    page_val = row.get('page') or row.get('pagina') or row.get('Página')
                    
                    # Determina status pelo mapeamento de páginas
                    status_val = get_status_from_page(page_val) if page_val else 'STATUS_01'

                    # No novo formato, tentamos usar nomes de colunas do DictReader
                    # Se falhar (CSV sem header padrão), usamos fallback de índices parciais
                    name = row.get('req_nome') or row.get('Nome') or "Desconhecido"
                    req_id = row.get('req_id') or row.get('ID') or f"REQ-{secrets.token_hex(4)}"

                    app_obj = BpiApplicant(
                        req_id=req_id,
                        name=name,
                        suffix=row.get('req_tipo', ''),
                        category=row.get('categoria', 'Empresa'),
                        country=row.get('req_pais', 'Moçambique'),
                        detected_year=row.get('ano', '2023'),
                        page=int(page_val) if page_val else None,
                        status=status_val
                    )
                    
                    # Evitar duplicados se o req_id já existir
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if not existing:
                        db.session.add(app_obj)
                        count += 1
            
            db.session.commit()
            print(f"✅ SUCESSO! {count} Requerentes importados e categorizados por status.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na importação: {e}")

def import_status_09():
    print("🚀 Importando Detalhamento de Alterações (STATUS_09)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_09.csv")
    
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo {file_path} não encontrado.")
        return

    with app.app_context():
        new_count = 0
        update_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    if not req_id: continue
                    
                    name = row.get('requerente') or "Titular Indeterminado"
                    
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if not existing:
                        app_obj = BpiApplicant(
                            req_id=req_id,
                            name=name,
                            brand_name=row.get('marca'),
                            filing_date=row.get('data_deposito'),
                            publication_date_bpi=row.get('data_publicacao_bpi'),
                            nice_class=row.get('classe_nice'),
                            status=row.get('codigo_status', 'STATUS_09'),
                            observations=row.get('observacoes'),
                            next_action=row.get('proxima_acao'),
                            deadline=row.get('prazo_limite'),
                            alteration_type=row.get('tipo_alteracao'),
                            alteration_details=row.get('detalhes_alteracao'),
                            category='Empresa',
                            country='Moçambique'
                        )
                        db.session.add(app_obj)
                        new_count += 1
                    else:
                        # Atualizar campos se já existir
                        existing.status = row.get('codigo_status', 'STATUS_09')
                        existing.alteration_type = row.get('tipo_alteracao')
                        existing.alteration_details = row.get('detalhes_alteracao')
                        existing.brand_name = row.get('marca')
                        # Se o nome original era genérico, atualiza
                        if existing.name == "Desconhecido" or not existing.name:
                            existing.name = name
                        update_count += 1
                
                db.session.commit()
                print(f"✅ SUCESSO! Alterações (STATUS_09): {new_count} novos, {update_count} atualizados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_09: {e}")

def import_status_01():
    print("🚀 Importando Publicações (STATUS_01)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_01.csv")
    
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo {file_path} não encontrado.")
        return

    with app.app_context():
        new_count = 0
        update_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    if not req_id: continue
                    name = row.get('requerente') or "Titular Indeterminado"
                    
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if not existing:
                        app_obj = BpiApplicant(
                            req_id=req_id,
                            name=name,
                            brand_name=row.get('marca'),
                            filing_date=row.get('data_deposito'),
                            publication_date_bpi=row.get('data_publicacao_bpi'),
                            nice_class=row.get('classe_nice'),
                            status='STATUS_01',
                            observations=row.get('observacoes'),
                            next_action=row.get('proxima_acao'),
                            deadline=row.get('prazo_limite'),
                            opposition_deadline=row.get('prazo_oposicao'),
                            category='Empresa',
                            country='Moçambique'
                        )
                        db.session.add(app_obj)
                        new_count += 1
                    else:
                        existing.status = 'STATUS_01'
                        existing.opposition_deadline = row.get('prazo_oposicao')
                        if existing.name == "Desconhecido": existing.name = name
                        update_count += 1
                
                db.session.commit()
                print(f"✅ SUCESSO! Publicações (STATUS_01): {new_count} novos, {update_count} atualizados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_01: {e}")

def import_status_02():
    print("🚀 Importando Concessões (STATUS_02)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_02.csv")
    
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo {file_path} não encontrado.")
        return

    with app.app_context():
        new_count = 0
        update_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    if not req_id: continue
                    name = row.get('requerente') or "Titular Indeterminado"
                    
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if not existing:
                        app_obj = BpiApplicant(
                            req_id=req_id,
                            name=name,
                            brand_name=row.get('marca'),
                            filing_date=row.get('data_deposito'),
                            publication_date_bpi=row.get('data_publicacao_bpi'),
                            nice_class=row.get('classe_nice'),
                            status='STATUS_02',
                            observations=row.get('observacoes'),
                            next_action=row.get('proxima_acao'),
                            deadline=row.get('prazo_limite'),
                            grant_date=row.get('data_concessao_estimada') or row.get('data_proxima_diu'),
                            category='Empresa',
                            country='Moçambique'
                        )
                        db.session.add(app_obj)
                        new_count += 1
                    else:
                        existing.status = 'STATUS_02'
                        existing.brand_name = row.get('marca')
                        existing.grant_date = row.get('data_concessao_estimada') or row.get('data_proxima_diu')
                        if existing.name == "Desconhecido": existing.name = name
                        update_count += 1
                
                db.session.commit()
                print(f"✅ SUCESSO! Concessões (STATUS_02): {new_count} novos, {update_count} atualizados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_02: {e}")

def import_status_03():
    print("🚀 Importando Renovações (STATUS_03)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_03.csv")
    
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo {file_path} não encontrado.")
        return

    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    name = row.get('requerente') or "Titular Indeterminado"
                    
                    app_obj = BpiApplicant(
                        req_id=req_id,
                        name=name,
                        brand_name=row.get('marca'),
                        filing_date=row.get('data_deposito'),
                        publication_date_bpi=row.get('data_publicacao_bpi'),
                        nice_class=row.get('classe_nice'),
                        status='STATUS_03',
                        observations=row.get('observacoes'),
                        next_action=row.get('proxima_acao'),
                        deadline=row.get('prazo_limite'),
                        renewal_date=row.get('data_renovacao'),
                        next_renewal_date=row.get('data_proxima_renovacao'),
                        category='Empresa',
                        country='Moçambique'
                    )
                    
                    # Evitar duplicados
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if not existing:
                        db.session.add(app_obj)
                        count += 1
                    else:
                        # Atualizar se necessário
                        existing.status = 'STATUS_03'
                        existing.next_renewal_date = row.get('data_proxima_renovacao')
                
                db.session.commit()
                print(f"✅ SUCESSO! {count} Renovações (STATUS_03) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_03: {e}")

def import_status_04():
    print("🚀 Importando Recusas Provisórias (STATUS_04)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_04.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    app_obj = BpiApplicant(
                        req_id=req_id, name=row.get('requerente'), brand_name=row.get('marca'),
                        filing_date=row.get('data_deposito'), publication_date_bpi=row.get('data_publicacao_bpi'),
                        nice_class=row.get('classe_nice'), status='STATUS_04',
                        appeal_deadline=row.get('prazo_recurso'), refusal_reason=row.get('motivo_recusa'),
                        next_action=row.get('proxima_acao'), category='Empresa', country='Moçambique'
                    )
                    if not BpiApplicant.query.filter_by(req_id=req_id).first():
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Recusas Provisórias (STATUS_04) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_04: {e}")

def import_status_05():
    print("🚀 Importando Renúncias (STATUS_05)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_05.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    app_obj = BpiApplicant(
                        req_id=req_id, name=row.get('requerente'), brand_name=row.get('marca'),
                        status='STATUS_05', renunciation_date=row.get('data_renuncia'),
                        category='Empresa', country='Moçambique'
                    )
                    if not BpiApplicant.query.filter_by(req_id=req_id).first():
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Renúncias (STATUS_05) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_05: {e}")

def import_status_06():
    print("🚀 Importando Recusas Definitivas (STATUS_06)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_06.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    app_obj = BpiApplicant(
                        req_id=req_id, name=row.get('requerente'), brand_name=row.get('marca'),
                        status='STATUS_06', final_refusal_date=row.get('data_recusa_definitiva'),
                        observations=row.get('observacoes'), category='Empresa', country='Moçambique'
                    )
                    if not BpiApplicant.query.filter_by(req_id=req_id).first():
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Recusas Definitivas (STATUS_06) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_06: {e}")

def import_status_07():
    print("🚀 Importando Avisos de Caducidade (STATUS_07)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_07.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    app_obj = BpiApplicant(
                        req_id=req_id, name=row.get('requerente'), brand_name=row.get('marca'),
                        status='STATUS_07', expiry_date=row.get('data_vencimento'),
                        renewal_deadline=row.get('prazo_renovacao'), triple_fee=row.get('taxa_tripla'),
                        next_action=row.get('proxima_acao'), observations=row.get('observacoes'),
                        category='Empresa', country='Moçambique'
                    )
                    if not BpiApplicant.query.filter_by(req_id=req_id).first():
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Avisos de Caducidade (STATUS_07) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_07: {e}")

def import_status_08():
    print("🚀 Importando Caducidade Definitiva (STATUS_08)...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "status_08.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    app_obj = BpiApplicant(
                        req_id=req_id, name=row.get('requerente'), brand_name=row.get('marca'),
                        status='STATUS_08', definite_expiry_date=row.get('data_caducidade'),
                        next_action=row.get('proxima_acao'), observations=row.get('observacoes'),
                        category='Empresa', country='Moçambique'
                    )
                    if not BpiApplicant.query.filter_by(req_id=req_id).first():
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Caducidade Definitiva (STATUS_08) processadas.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_status_08: {e}")

def import_requerentes_master():
    print("🚀 Importando Diretório Mestre de Requerentes...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "todos_requerentes.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Usamos o nome como chave para evitar duplicados se já houver processos desse requerente
                    name = row.get('nome_requerente')
                    existing = BpiApplicant.query.filter_by(name=name).first()
                    
                    if existing:
                        # Atualiza o perfil se já existir (vindo de um processo)
                        existing.nationality = row.get('nacionalidade')
                        existing.full_address = row.get('endereco_completo')
                        existing.total_processes = int(row.get('total_processos') or 0)
                    else:
                        # Cria um novo registro de diretório
                        app_obj = BpiApplicant(
                            req_id=f"DIR-{row.get('id_requerente')}",
                            name=name,
                            nationality=row.get('nacionalidade'),
                            full_address=row.get('endereco_completo'),
                            total_processes=int(row.get('total_processos') or 0),
                            status='MASTER',
                            category='Empresa',
                            country='Moçambique'
                        )
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Requerentes mestres processados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_requerentes_master: {e}")

def import_requerentes_processos():
    print("🚀 Importando Relação Requerentes x Processos...")
    base_dir = r"c:\Users\Acer\Documents\tecnologias\brandguardian\bpi"
    file_path = os.path.join(base_dir, "requerentes_processos.csv")
    if not os.path.exists(file_path): return
    with app.app_context():
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    req_id = row.get('numero_processo')
                    name = row.get('nome_requerente')
                    status_raw = row.get('status')
                    
                    # Mapeamento simples de status do CSV para nossos códigos
                    status_map = {
                        'PUBLICADO': 'STATUS_01',
                        'CONCEDIDO': 'STATUS_02',
                        'RENOVADO': 'STATUS_03',
                        'RECUSA_PROVISORIA': 'STATUS_04',
                        'RENUNCIADO': 'STATUS_05',
                        'RECUSA_DEFINITIVA': 'STATUS_06',
                        'AVISO_CADUCIDADE': 'STATUS_07',
                        'CADUCO_DEFINITIVO': 'STATUS_08',
                        'ALTERADO': 'STATUS_09'
                    }
                    
                    status_val = status_map.get(status_raw, 'STATUS_01')
                    
                    existing = BpiApplicant.query.filter_by(req_id=req_id).first()
                    if existing:
                        existing.name = name
                        existing.status = status_val
                        if row.get('data_deposito'):
                            existing.filing_date = row.get('data_deposito')
                    else:
                        app_obj = BpiApplicant(
                            req_id=req_id,
                            name=name,
                            status=status_val,
                            filing_date=row.get('data_deposito'),
                            category='Empresa',
                            country='Moçambique'
                        )
                        db.session.add(app_obj)
                        count += 1
            db.session.commit()
            print(f"✅ SUCESSO! {count} Processos vinculados processados.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro import_requerentes_processos: {e}")

if __name__ == '__main__':
    # 1. Carrega o diretório mestre de requerentes (Perfil)
    import_requerentes_master()
    # 2. Carrega a relação de processos x requerentes (Vínculo básico)
    import_requerentes_processos()
    # 3. Enriquece com os detalhes específicos de cada status
    import_status_01()
    import_status_03()
    import_status_04()
    import_status_05()
    import_status_06()
    import_status_07()
    import_status_08()
    import_status_09()
    # 4. Importação original baseada em páginas (opcional/fallback)
    import_applicants()
