import re
from datetime import datetime
from modules.constants import BrandStatus

class NormalizationMotor:
    @staticmethod
    def normalize_company_name(name):
        """
        ETAPA 4: Resolver inconsistências de nomes.
        Ex: 'Lda' -> 'LIMITADA'
        """
        if not name: return ""
        
        name = name.strip().upper()
        
        # Mapeamento de Alias / Equivalência
        replacements = {
            r'\bLDA\b': 'LIMITADA',
            r'\bLTDA\b': 'LIMITADA',
            r'\bLIMITADA\b': 'LIMITADA', # Garantir consistência
            r'\bS\.A\.\b': 'SA',
            r'\bS\.A\b': 'SA',
            r'\bSARL\b': 'S.A.R.L.',
            r'\bINC\b': 'INCORPORATED',
            r'\bLTD\b': 'LIMITED'
        }
        
        for pattern, replacement in replacements.items():
            name = re.sub(pattern, replacement, name)
            
        return " ".join(name.split())

    @staticmethod
    def normalize_nice_class(class_val):
        """
        ETAPA 4: Purificar classes.
        Ex: 'Classe 32' -> '32'
        """
        if not class_val: return "0"
        
        # Extrair apenas os dígitos
        match = re.search(r'\d+', str(class_val))
        if match:
            return match.group(0)
        return "0"

    @staticmethod
    def normalize_status(bpi_status):
        """
        ETAPA 5: Converter publicações em estados jurídicos claros.
        """
        if not bpi_status:
            return BrandStatus.DEPOSITADA
        
        s = str(bpi_status).lower()
        
        mapping = {
            'aviso': BrandStatus.PUBLICADA,
            'publicado': BrandStatus.PUBLICADA,
            'concessao': BrandStatus.CONCEDIDA,
            'concedido': BrandStatus.CONCEDIDA,
            'recusa provisoria': BrandStatus.RECUSA_PROVISORIA,
            'recusa definitiva': BrandStatus.RECUSA_DEFINITIVA,
            'caducidade': BrandStatus.CADUCADA,
            'caducado': BrandStatus.CADUCADA,
            'renovação': BrandStatus.RENOVADA,
            'renovado': BrandStatus.RENOVADA,
            'oposição': BrandStatus.OPOSICAO,
            'exame': BrandStatus.EXAMINADA,
            'corrigida': BrandStatus.CORRIGIDA,
            'depositada': BrandStatus.DEPOSITADA
        }
        
        for key, value in mapping.items():
            if key in s:
                return value
                
        return BrandStatus.DEPOSITADA

    @staticmethod
    def normalize_date(date_val):
        """
        ETAPA 4: Normalizar Datas para ISO (YYYY-MM-DD)
        """
        if not date_val: return ""
        if isinstance(date_val, datetime):
            return date_val.strftime('%Y-%m-%d')
            
        ds = str(date_val).strip()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(ds, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return ds

    @staticmethod
    def normalize_brand_type(brand_type):
        bt = str(brand_type).upper()
        if 'MIST' in bt: return 'Mista'
        if 'NOM' in bt: return 'Nominativa'
        if 'FIG' in bt: return 'Figurativa'
        return 'Nominativa'
