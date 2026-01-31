import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote_plus


class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def search_brand(self, brand_name):
        """Busca a marca na web (Google, INPI simulado)"""
        results = []

        try:
            # 1. Busca Google (simulada)
            google_results = self.search_google(brand_name)
            results.extend(google_results)

            # 2. Verificar domínios
            domain_results = self.check_domains(brand_name)
            results.extend(domain_results)

            # 3. Busca em redes sociais (simulada)
            social_results = self.check_social_media(brand_name)
            results.extend(social_results)

        except Exception as e:
            print(f"Erro na varredura web: {e}")

        return results

    def search_google(self, query, max_results=5):
        """Busca no Google (usando requests + BeautifulSoup)"""
        results = []
        try:
            url = f"https://www.google.com/search?q={quote_plus(query + ' marca registrada')}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            for g in soup.find_all('div', class_='g')[:max_results]:
                title = g.find('h3')
                link = g.find('a')
                snippet = g.find('div', class_='VwiC3b')

                if title and link:
                    results.append({
                        'source': 'Google',
                        'title': title.text,
                        'url': link['href'],
                        'snippet': snippet.text if snippet else '',
                        'relevance': 'medium'
                    })

        except Exception as e:
            print(f"Erro na busca Google: {e}")

        return results

    def check_domains(self, brand_name):
        """Verifica domínios disponíveis (simulação)"""
        domains = ['.pt', '.com', '.com.br', '.org']
        results = []

        for ext in domains:
            domain = f"{brand_name.lower().replace(' ', '')}{ext}"
            # Simulação - em produção usar API de WHOIS
            status = 'registrado' if hash(domain) % 3 == 0 else 'disponível'

            results.append({
                'source': 'Domínio',
                'title': domain,
                'url': f'http://{domain}',
                'snippet': f'Status: {status.upper()}',
                'relevance': 'high' if status == 'registrado' else 'low'
            })

        return results

    def check_social_media(self, brand_name):
        """Verifica redes sociais (simulação)"""
        platforms = ['Instagram', 'Facebook', 'Twitter', 'LinkedIn']
        results = []

        for platform in platforms:
            # Simulação - em produção usar APIs oficiais
            exists = hash(f"{brand_name}{platform}") % 4 == 0

            if exists:
                results.append({
                    'source': platform,
                    'title': f'{brand_name} em {platform}',
                    'url': f'https://{platform.lower()}.com/{brand_name.lower().replace(" ", "")}',
                    'snippet': f'Página encontrada em {platform}',
                    'relevance': 'medium'
                })

        return results

    def search_inpi_simulated(self, brand_name):
        """Simulação de busca no INPI Portugal"""
        # Nota: Para produção, integrar com API real ou web scraping do site do INPI
        return [{
            'source': 'INPI (Simulado)',
            'title': f'Marca similar: {brand_name} Solutions',
            'url': 'https://inpi.pt',
            'snippet': 'Classe 35 - Registro ativo',
            'relevance': 'high'
        }]