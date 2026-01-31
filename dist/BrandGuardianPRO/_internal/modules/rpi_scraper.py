"""
Módulo de Scraping da RPI (Revista da Propriedade Industrial)
Monitora publicações semanais do INPI para detectar novos pedidos e despachos
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json

class RPIScraper:
    def __init__(self):
        self.base_url = "https://www.inpi.gov.br/servicos/marcas/rpi-marcas"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_latest_rpi(self):
        """Obtém informações da última RPI publicada"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Procurar pelo link da última RPI
            # Formato típico: "RPI 2756 de 30/01/2024"
            rpi_links = soup.find_all('a', href=re.compile(r'rpi.*\.pdf', re.I))
            
            if rpi_links:
                latest = rpi_links[0]
                rpi_text = latest.get_text()
                
                # Extrair número e data
                match = re.search(r'RPI\s+(\d+).*?(\d{2}/\d{2}/\d{4})', rpi_text)
                if match:
                    rpi_number = match.group(1)
                    date_str = match.group(2)
                    publication_date = datetime.strptime(date_str, '%d/%m/%Y')
                    pdf_url = latest['href']
                    
                    return {
                        'rpi_number': f"RPI {rpi_number}",
                        'publication_date': publication_date,
                        'pdf_url': pdf_url,
                        'status': 'found'
                    }
            
            return {'status': 'not_found', 'message': 'Nenhuma RPI encontrada'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def download_rpi_pdf(self, pdf_url, save_path):
        """Faz download do PDF da RPI"""
        try:
            response = requests.get(pdf_url, headers=self.headers, timeout=60, stream=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Erro ao baixar PDF: {e}")
            return False
    
    def parse_rpi_text(self, text_content):
        """
        Parseia o conteúdo textual da RPI para extrair pedidos de marca
        Nota: Requer conversão de PDF para texto primeiro
        """
        new_marks = []
        
        # Padrão típico de pedido de marca no INPI:
        # Número: 123456789
        # Apresentação: Nominativa
        # Marca: NOME DA MARCA
        # Classe(s): 35
        
        pattern = r'N[úu]mero:\s*(\d+).*?Marca:\s*([^\n]+).*?Classe.*?(\d+(?:,\s*\d+)*)'
        matches = re.finditer(pattern, text_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            new_marks.append({
                'process_number': match.group(1),
                'mark_name': match.group(2).strip(),
                'classes': match.group(3).strip()
            })
        
        return new_marks
    
    def detect_conflicts(self, new_marks, existing_brands):
        """
        Compara novos pedidos com marcas existentes do cliente
        Retorna lista de possíveis conflitos
        """
        from modules.brand_analyzer import BrandAnalyzer
        analyzer = BrandAnalyzer()
        
        conflicts = []
        
        for new_mark in new_marks:
            for brand in existing_brands:
                # Verificar se as classes se sobrepõem
                new_classes = set(new_mark['classes'].split(','))
                brand_classes = set(str(brand.nice_classes).split(','))
                
                if new_classes.intersection(brand_classes):
                    # Calcular similaridade
                    similarity = analyzer.calculate_text_similarity(
                        new_mark['mark_name'], 
                        brand.name
                    )
                    
                    if similarity > 0.6:  # 60% de similaridade
                        conflicts.append({
                            'brand_id': brand.id,
                            'brand_name': brand.name,
                            'conflicting_mark': new_mark['mark_name'],
                            'conflicting_number': new_mark['process_number'],
                            'similarity_score': round(similarity * 100, 1),
                            'conflict_type': 'phonetic' if similarity > 0.8 else 'moderate'
                        })
        
        return conflicts
    
    def get_process_status(self, process_number):
        """
        Consulta o status de um processo específico no INPI
        (Simulação - implementar integração real com API/site do INPI)
        """
        # TODO: Implementar scraping real do site de busca do INPI
        # URL típica: https://busca.inpi.gov.br/pePI/servlet/MarcasServletController
        
        return {
            'process_number': process_number,
            'status': 'Em análise',
            'last_update': datetime.now().strftime('%d/%m/%Y'),
            'current_phase': 'Exame formal'
        }


# Função auxiliar para conversão de PDF para texto
def pdf_to_text(pdf_path):
    """
    Converte PDF da RPI para texto
    Requer: pip install PyPDF2 ou pdfplumber
    """
    try:
        import PyPDF2
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text
    except ImportError:
        print("PyPDF2 não instalado. Use: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"Erro ao converter PDF: {e}")
        return ""
