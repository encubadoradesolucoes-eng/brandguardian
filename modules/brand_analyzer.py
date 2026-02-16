import imagehash
from PIL import Image
import os
from difflib import SequenceMatcher
import json
from datetime import datetime
from modules.real_scanner import scan_live_real, verificacao_imagem_real  # IMPORTA O SCANNER REAL + VISUAL
import tempfile
import io

class BrandAnalyzer:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def analyze_brand(self, brand_id, db_session, BrandModel):
        """
        Analisa uma marca usando o motor REAL (scan_live_real) que verifica:
        1. BPI (Banco Oficial)
        2. Web (Domínios)
        3. Redes Sociais
        4. Clientes internos (M24)
        
        RETORNA EVIDÊNCIAS REAIS para justificar o score de risco.
        """
        # Obter a marca alvo da sessão
        target_brand = db_session.get(BrandModel, brand_id)
        if not target_brand:
            return []

        print(f">>> [REAL ANALYZER] Iniciando análise profunda para: {target_brand.name}")

        # 1. Executar o Scanner Real (O mesmo usado no Live e na Auditoria)
        try:
            # Passamos usuario_logado=True para ter detalhes completos
            resultados_reais = scan_live_real(target_brand.name, usuario_logado=True)
            
            # 2. Executar Análise Visual se houver imagem
            visual_matches = {}
            if target_brand.image_data:
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        tmp.write(target_brand.image_data)
                        tmp_path = tmp.name
                    
                    res_visual = verificacao_imagem_real(tmp_path, target_brand.name)
                    # Mapeia resultados por processo para facilitar junção
                    for v in res_visual.get('conflitos_visuais', []):
                        if v.get('processo'):
                            visual_matches[v['processo']] = v['similarity_final']
                    
                    # Limpa temporário
                    if os.path.exists(tmp_path): os.remove(tmp_path)
                except Exception as ve:
                    print(f"Erro na análise visual: {ve}")

            # 3. Interpretar Resultados para atualizar o Modelo da Marca
            risco_analise = resultados_reais.get('analise_risco', {})
            
            # Score atualizado do motor real (0 a 100)
            # Vamos recalcular o risco baseado no BPI + Visual se houver
            confi_bpi = resultados_reais.get('bpi', [])
            
            # Atualiza a marca no banco
            target_brand.last_analyzed = datetime.now()

            # Tenta extrair score visual e fonético dos componentes
            target_brand.phonetic_score = 0
            if confi_bpi:
                target_brand.phonetic_score = confi_bpi[0].get('similaridade', 0)
            
            # Pega o maior score visual encontrado
            target_brand.visual_score = max(visual_matches.values()) if visual_matches else 0
            
            # Recalcular score total: Média ponderada (70% Fonético/Texto, 30% Visual) se houver classe overlap
            # Se for EXATAMENTE a mesma marca por logo, risco sobe
            max_visual = target_brand.visual_score
            max_phonetic = target_brand.phonetic_score
            
            novo_score = max(max_phonetic, max_visual)
            if max_phonetic > 60 and max_visual > 60:
                novo_score = min(100, novo_score + 20) # Combinado é pior
                
            target_brand.risk_score = novo_score
            target_brand.risk_level = self.get_risk_level(novo_score)

            print(f">>> [REAL ANALYZER] Conclusão para {target_brand.name}: Risco {novo_score} (V:{max_visual} F:{max_phonetic})")
            
            # Retorna lista de "marcas similares" no formato antigo para compatibilidade com o frontend
            # AGORA COM DADOS REAIS E EVIDÊNCIAS
            similar_brands_compat = []
            
            # Adiciona domínios ocupados como "conflitos"
            dominios = resultados_reais.get('dominios', [])
            for dom in dominios:
                if dom['status'] == 'OCUPADO':
                    is_national = '.co.mz' in dom['dominio']
                    
                    # Calcular similaridade textual real
                    text_sim = self._calculate_text_similarity(target_brand.name, dom['dominio'].replace('.co.mz', '').replace('.com', ''))
                    
                    similar_brands_compat.append({
                        'brand': type('obj', (object,), {
                            'name': dom['dominio'], 
                            'id': 0, 
                            'logo_path': None, 
                            'nice_classes': 'WEB',
                            'owner_name': 'Proprietário Web',
                            'process_number': 'DNS-REGISTRY'
                        }),
                        'text_similarity': text_sim,
                        'visual_similarity': 0,
                        'class_overlap': 0,
                        'total_risk': max(text_sim, 90 if is_national else 60),
                        'risk_level': 'high' if is_national else 'medium',
                        'source': 'WEB',
                        'evidence': {
                            'phonetic_match': f"Domínio {dom['dominio']} está OCUPADO",
                            'visual_match': 'N/A (domínio web)',
                            'class_match': 'Presença digital conflitante'
                        }
                    })

            # Adiciona conflitos BPI COM EVIDÊNCIAS REAIS
            for bpi in confi_bpi:
                # Calcular similaridade textual detalhada
                text_sim = bpi['similaridade']
                
                # Calcular overlap de classe Nice
                target_classes = set(str(target_brand.nice_classes).split(',')) if target_brand.nice_classes else set()
                bpi_classes = set(str(bpi.get('classe', '')).split(','))
                class_overlap = len(target_classes & bpi_classes) / max(len(target_classes | bpi_classes), 1) * 100 if target_classes or bpi_classes else 0
                
                # Determinar nível de risco baseado em múltiplos fatores
                risk_factors = []
                if text_sim > 80:
                    risk_factors.append(f"Similaridade textual CRÍTICA: {text_sim}%")
                elif text_sim > 60:
                    risk_factors.append(f"Similaridade textual ALTA: {text_sim}%")
                else:
                    risk_factors.append(f"Similaridade textual moderada: {text_sim}%")
                
                if class_overlap > 50:
                    risk_factors.append(f"Overlap de classe Nice: {class_overlap:.0f}%")
                
                # Calcular risco total ponderado
                visual_sim = visual_matches.get(str(bpi.get('processo')), 0)
                
                # Se houver similaridade visual, adiciona fator
                if visual_sim > 70:
                    risk_factors.append(f"Similaridade VISUAL CRÍTICA: {visual_sim}%")
                elif visual_sim > 40:
                    risk_factors.append(f"Similaridade visual detectada: {visual_sim}%")

                total_risk = max(text_sim, visual_sim)
                if text_sim > 50 and visual_sim > 50:
                    total_risk = min(100, total_risk + 15)
                
                similar_brands_compat.append({
                    'brand': type('obj', (object,), {
                        'name': bpi['marca'], 
                        'id': bpi.get('id', 0), 
                        'logo_path': None, 
                        'nice_classes': str(bpi.get('classe')),
                        'owner_name': bpi.get('titular', 'Titular BPI'),
                        'process_number': str(bpi.get('processo'))
                    }),
                    'id': bpi.get('id', 0),
                    'logo_url': f"/api/get-image/ipi/{bpi.get('id')}" if bpi.get('id') else None,
                    'text_similarity': text_sim,
                    'visual_similarity': visual_sim,
                    'class_overlap': class_overlap, 
                    'total_risk': total_risk,
                    'risk_level': 'high' if total_risk > 70 else ('medium' if total_risk > 40 else 'low'),
                    'source': 'BPI',
                    'evidence': {
                        'phonetic_match': f"Marca '{bpi['marca']}' tem {text_sim}% de similaridade fonética",
                        'visual_match': f"Similaridade visual de {visual_sim}%" if visual_sim > 0 else 'Nenhuma similaridade visual significativa',
                        'class_match': f"Classes Nice: {bpi.get('classe')} (overlap: {class_overlap:.0f}%)",
                        'risk_factors': ' | '.join(risk_factors)
                    }
                })

            # Ordenar por risco total (maior primeiro)
            similar_brands_compat.sort(key=lambda x: x['total_risk'], reverse=True)

            db_session.commit()
            return similar_brands_compat
            
        except Exception as e:
            print(f"Erro no Real Analyzer: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_text_similarity(self, text1, text2):
        """Calcula similaridade textual usando SequenceMatcher"""
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        return round(SequenceMatcher(None, text1, text2).ratio() * 100, 1)

    def quick_analysis(self, brand_name, classes, db_session, BrandModel):
        """
        Versão rápida usando scan_live_real também.
        """
        try:
            resultados = scan_live_real(brand_name, usuario_logado=False)
            risco = resultados.get('analise_risco', {})
            
            conflicts = []
            # Adapter para formato antigo
            for bpi in resultados.get('bpi', [])[:5]:
                conflicts.append({
                    'existing_brand': bpi['marca'],
                    'similarity': bpi['similaridade'],
                    'classes': str(bpi.get('classe')),
                    'status': 'Registrado (BPI)'
                })
                
            return {
                'brand_name': brand_name,
                'risk_level': risco.get('nivel_risco', 'BAIXO').lower(),
                'conflicts_found': len(conflicts),
                'conflicts': conflicts,
                'recommendation': risco.get('recomendacao', 'Sem dados suficientes')
            }
        except:
            return {'brand_name': brand_name, 'risk_level': 'low', 'conflicts': []}

    def get_risk_level(self, score):
        if score >= 70: return 'high'
        if score >= 40: return 'medium'
        return 'low'

    def get_recommendation(self, risk_level, conflicts):
        if risk_level == 'high': return "Alto risco detectado."
        return "Risco baixo."