import re
from datetime import datetime
from modules.constants import BrandStatus

def normalize_name(name: str) -> str:
    """Normaliza nomes de empresas e marcas."""
    if not name:
        return ""
    
    # Remove espaços extras
    name = " ".join(name.split())
    
    # Mapeamento de sufíxos
    replacements = {
        r'\bLda\b': 'Limitada',
        r'\bSA\b': 'S.A.',
        r'\bS\.A\b': 'S.A.',
        r'\bSARL\b': 'S.A.R.L.',
        r'\bInc\b': 'Incorporated',
        r'\bLtd\b': 'Limited'
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
    
    return name

def normalize_status(bpi_status: str) -> str:
    """Mapeia o jargão do BPI para o ENUM da plataforma."""
    if not bpi_status:
        return BrandStatus.DEPOSITADA
    
    bpi_status = bpi_status.lower()
    
    mapping = {
        'aviso': BrandStatus.PUBLICADA,
        'concessao': BrandStatus.CONCEDIDA,
        'concedido': BrandStatus.CONCEDIDA,
        'recusa provisoria': BrandStatus.RECUSA_PROVISORIA,
        'recusa definitiva': BrandStatus.RECUSA_DEFINITIVA,
        'caducidade': BrandStatus.CADUCADA,
        'caducado': BrandStatus.CADUCADA,
        'renovação': BrandStatus.RENOVADA,
        'renovado': BrandStatus.RENOVADA,
        'oposição': BrandStatus.OPOSICAO,
        'exame': BrandStatus.EXAMINADA
    }
    
    for key, value in mapping.items():
        if key in bpi_status:
            return value
            
    return BrandStatus.DEPOSITADA

def normalize_date(date_val) -> str:
    """Garante que a data esteja no formato ISO YYYY-MM-DD."""
    if not date_val:
        return ""
    
    if isinstance(date_val, datetime):
        return date_val.strftime('%Y-%m-%d')
    
    # Se for string, tenta converter vários formatos comuns
    date_str = str(date_val).strip()
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    return date_str # Retorna original se falhar
