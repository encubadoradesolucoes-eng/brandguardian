import imagehash
from PIL import Image
import os
# Imports movidos para dentro do método para evitar ciclo com app.py

class DuplicateImageFinder:
    def __init__(self, app_root):
        # app_root deve ser o caminho raiz da aplicação
        self.base_path = app_root
    
    def find_duplicate_images(self, target_image_path, threshold=12):
        """
        Encontra imagens idênticas ou muito similares (pHash)
        threshold=10 é um bom balanço. 0 = idêntico.
        """
        try:
            from app import Brand
            # Calcular hash da imagem alvo
            target_img = Image.open(target_image_path)
            target_hash = imagehash.phash(target_img)
            
            results = []
            
            # Buscar marcas que tem logo
            brands = Brand.query.filter(Brand.logo_path.isnot(None)).all()
            
            for brand in brands:
                if brand.logo_path:
                    # Caminho varia dependendo de como foi salvo (absoluto ou relativo)
                    # O sistema salva em 'static/uploads' ou 'uploads'
                    # Vamos tentar construir o caminho absoluto
                    
                    # Tentar static/uploads primeiro (padrão do BrandGuardian)
                    logo_path = os.path.join(self.base_path, 'static', 'uploads', brand.logo_path)
                    
                    if not os.path.exists(logo_path):
                        # Tentar caminho alternativo 'uploads' na raiz
                        logo_path = os.path.join(self.base_path, 'uploads', brand.logo_path)
                    
                    if os.path.exists(logo_path):
                        try:
                            existing_img = Image.open(logo_path)
                            existing_hash = imagehash.phash(existing_img)
                            
                            hamming_distance = target_hash - existing_hash
                            
                            if hamming_distance <= threshold:
                                # Normalizar similaridade (aprox)
                                # pHash tem 64 bits. Distancia 0 = 100%. 
                                similarity = max(0, 100 - (hamming_distance * 100 / 32)) 
                                
                                results.append({
                                    'brand_name': brand.name,
                                    'owner': brand.owner_name,
                                    'similarity': int(similarity),
                                    'distance': hamming_distance,
                                    'status': 'ALTO RISCO' if hamming_distance < 5 else 'MODERADO',
                                    'logo_url': brand.logo_path
                                })
                        except Exception as e:
                            # Imagem corrompida ou ilegível, pula
                            continue
            
            # --- BUSCA NA BASE BPI (IPIRecord) ---
            from app import IpiRecord
            ipi_records = IpiRecord.query.filter(IpiRecord.image_path.isnot(None)).all()
            
            for rec in ipi_records:
                if rec.image_path:
                    # Caminho dos logos IPI: static/ipi_images
                    logo_path = os.path.join(self.base_path, 'static', 'ipi_images', rec.image_path)
                    
                    if os.path.exists(logo_path):
                        try:
                            existing_img = Image.open(logo_path)
                            existing_hash = imagehash.phash(existing_img)
                            
                            hamming_distance = target_hash - existing_hash
                            
                            if hamming_distance <= threshold:
                                similarity = max(0, 100 - (hamming_distance * 100 / 32)) 
                                
                                results.append({
                                    'brand_name': rec.brand_name,
                                    'owner': rec.applicant_name,
                                    'similarity': int(similarity),
                                    'distance': hamming_distance,
                                    'status': f'BPI OFICIAL (Proc: {rec.process_number})',
                                    'logo_url': f'ipi_images/{rec.image_path}'
                                })
                        except:
                            continue

            # Ordenar por similaridade
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Erro no ImageHasher: {e}")
            return []
