import imagehash
from PIL import Image, ImageOps
import os
import io
from typing import Dict, List, Optional, Any

class DuplicateImageFinder:
    def __init__(self, app_root):
        # app_root deve ser o caminho raiz da aplicação
        self.base_path = app_root
    
    def find_duplicate_images(self, target_image_path, threshold=12, brand_records=None, ipi_records=None):
        """
        Encontra imagens idênticas ou muito similares usando múltiplos algoritmos de hash.
        
        Args:
            target_image_path: Caminho da imagem a verificar
            threshold: Limiar de distância (menor = mais similar). 0 = idêntico, 12 = moderado
            brand_records: Lista de dicionários com {id, name, logo_path} das marcas de usuários
            ipi_records: Lista de dicionários com {id, application_number, image_path} dos registros BPI
        
        Returns:
            Lista de resultados com similaridade
        """
        try:
            
            # Calcular múltiplos hashes da imagem alvo para maior precisão
            target_img = Image.open(target_image_path)
            target_hash_avg = imagehash.average_hash(target_img)
            target_hash_phash = imagehash.phash(target_img)
            target_hash_dhash = imagehash.dhash(target_img)
            
            results = []
            
            # ========== BUSCA EM MARCAS DE USUÁRIOS ==========
            if brand_records:
                print(f"🔍 Comparando com {len(brand_records)} marcas de usuários via banco de dados...")
                
                for brand in brand_records:
                    if brand.get('image_data'):
                        # Carrega binário diretamente do banco
                        img_io = io.BytesIO(brand['image_data'])
                        conflito = self._compare_images_bin(
                            img_io,
                            target_hash_avg,
                            target_hash_phash,
                            target_hash_dhash,
                            threshold
                        )
                        
                        if conflito:
                            print(f"   ⚠️  Conflito encontrado: {brand['name']} ({conflito['similarity_final']}%)")
                            results.append({
                                'brand_name': brand['name'],
                                'owner': brand.get('owner_name') or 'N/A',
                                'similarity_avg': conflito['similarity_avg'],
                                'similarity_phash': conflito['similarity_phash'],
                                'similarity_dhash': conflito['similarity_dhash'],
                                'similarity_final': conflito['similarity_final'],
                                'status': f'MARCA USUÁRIO (ID: {brand["id"]})',
                                'gravidade': conflito['gravidade'],
                                'logo_url': f"/api/get-image/brand/{brand['id']}", # URL para renderizar do banco
                                'tipo': 'USER_BRAND'
                            })
            
            # ========== BUSCA NA BASE BPI (IPIRecord) ==========
            if ipi_records:
                print(f"🔍 Comparando com {len(ipi_records)} registros BPI via banco de dados...")
                
                for rec in ipi_records:
                    if rec.get('image_data'):
                        # Carrega binário diretamente do banco
                        img_io = io.BytesIO(rec['image_data'])
                        conflito = self._compare_images_bin(
                            img_io,
                            target_hash_avg,
                            target_hash_phash,
                            target_hash_dhash,
                            threshold
                        )
                        
                        if conflito:
                            results.append({
                                'brand_name': rec.get('brand_name') or 'Desconhecida',
                                'owner': rec.get('applicant_name') or 'N/A',
                                'similarity_avg': conflito['similarity_avg'],
                                'similarity_phash': conflito['similarity_phash'],
                                'similarity_dhash': conflito['similarity_dhash'],
                                'similarity_final': conflito['similarity_final'],
                                'status': f'BPI OFICIAL (Proc: {rec.get("process_number") or "N/A"})',
                                'gravidade': conflito['gravidade'],
                                'logo_url': f"/api/get-image/ipi/{rec['id']}", # URL para renderizar do banco
                                'tipo': 'BPI_RECORD',
                                'processo': rec.get('process_number')
                            })

            # Ordenar por similaridade final (média dos 3 algoritmos)
            results.sort(key=lambda x: x['similarity_final'], reverse=True)
            return results
            
        except Exception as e:
            print(f"❌ Erro no DuplicateImageFinder: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _resolve_logo_path(self, relative_path: str, search_dirs: List[str]) -> Optional[str]:
        """Resolve o caminho completo do logo tentando múltiplos diretórios."""
        # Se já for caminho absoluto e existir
        if os.path.isabs(relative_path):
            if os.path.exists(relative_path):
                return relative_path
            # Se absoluto mas não existe, pode ser que só o filename seja usado
            relative_path = os.path.basename(relative_path)
        
        # Tenta em cada diretório
        for search_dir in search_dirs:
            full_path = os.path.join(self.base_path, search_dir, relative_path)
            if os.path.exists(full_path):
                return full_path
        
        # Última tentativa: relativo ao base_path diretamente
        direct_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(direct_path):
            return direct_path
        
        return None
    
    def _compare_images_bin(self, image_io, target_avg, target_phash, target_dhash, threshold: int) -> Optional[Dict]:
        """Compara uma imagem binária (BytesIO) usando 3 algoritmos de hash."""
        try:
            img = Image.open(image_io)
            
            # Gera os 3 hashes
            hash_avg = imagehash.average_hash(img)
            hash_phash = imagehash.phash(img)
            hash_dhash = imagehash.dhash(img)
            
            # Calcula distâncias
            dist_avg = target_avg - hash_avg
            dist_phash = target_phash - hash_phash
            dist_dhash = target_dhash - hash_dhash
            
            # Se pelo menos um algoritmo detectar similaridade
            if min(dist_avg, dist_phash, dist_dhash) <= threshold:
                # Calcula similaridades em %
                sim_avg = max(0, 100 - (dist_avg * 100 / 64))
                sim_phash = max(0, 100 - (dist_phash * 100 / 64))
                sim_dhash = max(0, 100 - (dist_dhash * 100 / 64))
                
                # Média ponderada (pHash é geralmente mais confiável)
                sim_final = (sim_avg * 0.2 + sim_phash * 0.5 + sim_dhash * 0.3)
                
                # Define gravidade
                if sim_final >= 85:
                    gravidade = 'CRÍTICA'
                elif sim_final >= 75:
                    gravidade = 'ALTA'
                elif sim_final >= 65:
                    gravidade = 'MÉDIA'
                else:
                    gravidade = 'BAIXA'
                
                return {
                    'similarity_avg': round(sim_avg, 1),
                    'similarity_phash': round(sim_phash, 1),
                    'similarity_dhash': round(sim_dhash, 1),
                    'similarity_final': round(sim_final, 1),
                    'gravidade': gravidade
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  Erro ao comparar imagem binária: {e}")
            return None

    def _compare_images(self, image_path: str, target_avg, target_phash, target_dhash, threshold: int) -> Optional[Dict]:
        """Compara uma imagem física usando 3 algoritmos de hash."""
        try:
            with open(image_path, 'rb') as f:
                img_io = io.BytesIO(f.read())
                return self._compare_images_bin(img_io, target_avg, target_phash, target_dhash, threshold)
        except Exception as e:
            print(f"⚠️  Erro ao carregar arquivo {image_path}: {e}")
            return None
