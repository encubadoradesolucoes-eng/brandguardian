import imagehash
from PIL import Image
import os
from difflib import SequenceMatcher
import json
from datetime import datetime


class BrandAnalyzer:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def calculate_text_similarity(self, text1, text2):
        """Calcula similaridade textual entre 0 e 1"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def calculate_image_similarity(self, image_path1, image_path2):
        """Calcula similaridade entre imagens usando pHash"""
        try:
            if not image_path1 or not image_path2:
                return 0.0

            full_path1 = os.path.join(self.base_path, 'uploads', image_path1)
            full_path2 = os.path.join(self.base_path, 'uploads', image_path2)

            if not os.path.exists(full_path1) or not os.path.exists(full_path2):
                return 0.0

            hash1 = imagehash.phash(Image.open(full_path1))
            hash2 = imagehash.phash(Image.open(full_path2))

            # Distância normalizada (0 = idêntico, 1 = diferente)
            distance = hash1 - hash2
            similarity = max(0.0, 1.0 - (distance / 64.0))

            return similarity

        except Exception as e:
            print(f"Erro na comparação de imagens: {e}")
            return 0.0

    def class_overlap(self, classes1, classes2):
        """Calcula sobreposição de classes de Nice"""
        if not classes1 or not classes2:
            return 0.0

        set1 = set(str(classes1).split(','))
        set2 = set(str(classes2).split(','))

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        return len(intersection) / len(union) if union else 0.0

    def analyze_brand(self, brand_id, db_session, BrandModel):
        """Analisa uma marca contra todas as outras no banco de dados"""
        # Usar o método direto da sessão para evitar dependência de contexto automático
        target_brand = db_session.get(BrandModel, brand_id)
        if not target_brand:
            return []

        all_brands = db_session.query(BrandModel).filter(BrandModel.id != brand_id).all()
        similar_brands = []

        for brand in all_brands:
            # 1. Similaridade textual
            text_sim = self.calculate_text_similarity(target_brand.name, brand.name)

            # 2. Similaridade visual (se tiver logo)
            visual_sim = 0.0
            if target_brand.logo_path and brand.logo_path:
                visual_sim = self.calculate_image_similarity(target_brand.logo_path, brand.logo_path)

            # 3. Sobreposição de classes
            class_sim = self.class_overlap(target_brand.nice_classes, brand.nice_classes)

            # 4. Cálculo do risco combinado
            total_risk = (text_sim * 0.4 + visual_sim * 0.4 + class_sim * 0.2)
            
            # Ajuste de peso
            if text_sim > 0.8: total_risk = max(total_risk, 0.85)

            if total_risk > 0.3:
                similar_brands.append({
                    'brand': brand,
                    'text_similarity': round(text_sim * 100, 1),
                    'visual_similarity': round(visual_sim * 100, 1),
                    'class_overlap': round(class_sim * 100, 1),
                    'total_risk': round(total_risk * 100, 1),
                    'risk_level': self.get_risk_level(total_risk)
                })

        # Ordenar por risco
        similar_brands.sort(key=lambda x: x['total_risk'], reverse=True)

        if similar_brands:
            max_risk_item = similar_brands[0] # O mais alto ja esta no topo
            target_brand.risk_score = max_risk_item['total_risk']
            target_brand.risk_level = max_risk_item['risk_level']
            target_brand.phonetic_score = max_risk_item['text_similarity']
            target_brand.visual_score = max_risk_item['visual_similarity']
        else:
            target_brand.risk_score = 0
            target_brand.risk_level = 'low'
            target_brand.phonetic_score = 0
            target_brand.visual_score = 0

        target_brand.last_analyzed = datetime.now()
        db_session.commit()
        return similar_brands

    def quick_analysis(self, brand_name, classes, db_session, BrandModel):
        """Análise rápida para API pública"""
        all_brands = db_session.query(BrandModel).all()
        conflicts = []

        for brand in all_brands:
            text_sim = self.calculate_text_similarity(brand_name, brand.name)
            class_sim = self.class_overlap(','.join(map(str, classes)), brand.nice_classes)

            if text_sim > 0.7 or (text_sim > 0.5 and class_sim > 0.5):
                conflicts.append({
                    'existing_brand': brand.name,
                    'similarity': round(text_sim * 100, 1),
                    'classes': brand.nice_classes,
                    'status': brand.status
                })

        risk = 'high' if any(c['similarity'] > 80 for c in conflicts) else \
            'medium' if conflicts else 'low'

        return {
            'brand_name': brand_name,
            'risk_level': risk,
            'conflicts_found': len(conflicts),
            'conflicts': conflicts[:5],  # Limitar a 5
            'recommendation': self.get_recommendation(risk, conflicts)
        }

    def get_risk_level(self, score):
        """Converte score para nível de risco"""
        if score >= 0.7:  # 70%
            return 'high'
        elif score >= 0.4:  # 40%
            return 'medium'
        else:
            return 'low'

    def get_recommendation(self, risk_level, conflicts):
        """Gera recomendação baseada no risco"""
        if risk_level == 'high':
            return "Alto risco de rejeição. Considere alterar o nome ou consultar um especialista."
        elif risk_level == 'medium':
            return "Risco moderado. Recomenda-se verificação detalhada antes do registro."
        else:
            return "Risco baixo. O nome parece estar disponível para registro."