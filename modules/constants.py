# M24 Platform Constants (Based on TR)

class BrandStatus:
    DEPOSITADA = "DEPOSITADA"
    PUBLICADA = "PUBLICADA"
    EXAMINADA = "EXAMINADA"
    CONCEDIDA = "CONCEDIDA"
    RENOVADA = "RENOVADA"
    CORRIGIDA = "CORRIGIDA"
    RECUSA_PROVISORIA = "RECUSA_PROVISORIA"
    RECUSA_DEFINITIVA = "RECUSA_DEFINITIVA"
    CADUCADA = "CADUCADA"
    OPOSICAO = "OPOSICAO"

    @classmethod
    def all(cls):
        return [
            cls.DEPOSITADA, cls.PUBLICADA, cls.EXAMINADA, 
            cls.CONCEDIDA, cls.RENOVADA, cls.CORRIGIDA, 
            cls.RECUSA_PROVISORIA, cls.RECUSA_DEFINITIVA, 
            cls.CADUCADA, cls.OPOSICAO
        ]

class BrandType:
    NOMINATIVA = "Nominativa"
    FIGURATIVA = "Figurativa"
    MISTA = "Mista"

    @classmethod
    def all(cls):
        return [cls.NOMINATIVA, cls.FIGURATIVA, cls.MISTA]

# Priority for Alerts
class AlertPriority:
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    CRITICAL = "CRITICAL"
