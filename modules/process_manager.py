from app import db, Brand, BrandLog
from modules.normalizer import normalize_name, normalize_status, normalize_date
from modules.constants import BrandStatus
from datetime import datetime

def register_bpi_event(data: dict):
    """
    Registra um novo evento do BPI e atualiza o processo central.
    Segue a regra: 'Uma marca = um processo central + múltiplos eventos'.
    
    Args:
        data: Dicionário com dados do evento (numero_processo, nome, status, etc.)
    """
    process_number = data.get('process_number')
    if not process_number:
        return None, "Número de processo ausente."

    # Normalização dos dados
    name = normalize_name(data.get('name', ''))
    status = normalize_status(data.get('status', ''))
    filing_date = normalize_date(data.get('filing_date', ''))
    
    # 1. Verificar se a marca já existe
    brand = Brand.query.filter_by(process_number=process_number).first()
    
    if not brand:
        # Criar nova marca (Processo Central)
        brand = Brand(
            process_number=process_number,
            name=name,
            status=status,
            filing_date=filing_date,
            nice_classes=data.get('nice_classes'),
            owner_name=normalize_name(data.get('owner_name', '')),
            nationality=data.get('nationality'),
            full_address=data.get('full_address'),
            profession=data.get('profession'),
            brand_type=data.get('brand_type'),
            product_description=data.get('product_description'),
            submission_date=datetime.utcnow()
        )
        db.session.add(brand)
        db.session.flush() # Para pegar o ID
        action_desc = f"Processo inicializado via BPI: {status}"
    else:
        # Atualizar marca existente
        brand.status = status
        brand.last_analyzed = datetime.utcnow()
        
        # Atualiza campos se estiverem vazios ou se o novo evento for mais recente/detalhado
        if not brand.nice_classes: brand.nice_classes = data.get('nice_classes')
        if not brand.profession: brand.profession = data.get('profession')
        
        action_desc = f"Novo evento BPI detectado: {status}"

    # 2. Criar o Evento (BrandLog)
    log = BrandLog(
        brand_id=brand.id,
        action_type=status.lower(),
        description=data.get('observations') or action_desc,
        bulletin_number=data.get('bulletin_number'),
        event_date=datetime.utcnow()
    )
    db.session.add(log)
    
    try:
        db.session.commit()
        return brand, "Sucesso"
    except Exception as e:
        db.session.rollback()
        return None, str(e)
