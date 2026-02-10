"""
Verificação com logs detalhados em tempo real
"""
import os
import sys
import socket
import requests
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

def log(emoji, mensagem, indent=0):
    """Helper para logs formatados"""
    spaces = "  " * indent
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {spaces}{emoji} {mensagem}")

def verificar_termo_com_logs(termo: str):
    """Replica a lógica do scan_live_real mas com logs detalhados"""
    
    print("=" * 80)
    print(f"VERIFICAÇÃO DETALHADA: '{termo}'")
    print("=" * 80)
    print()
    
    # Normalização
    log("🔧", f"Normalizando termo: '{termo}'")
    termo_limpo = ''.join(c for c in termo.lower() if c.isalnum())
    log("✓", f"Termo limpo: '{termo_limpo}'", 1)
    print()
    
    # ===== DOMÍNIOS =====
    log("🌐", "FASE 1: Verificando Domínios")
    print()
    
    tlds = ['.co.mz', '.com', '.org', '.net', '.info']
    dominios_ocupados = []
    dominio_mz_ocupado = False
    
    for tld in tlds:
        dominio = f"{termo_limpo}{tld}"
        log("🔍", f"Testando: {dominio}", 1)
        
        try:
            inicio = time.time()
            ip = socket.gethostbyname(dominio)
            tempo = (time.time() - inicio) * 1000
            log("❌", f"OCUPADO - IP: {ip} ({tempo:.0f}ms)", 2)
            dominios_ocupados.append(dominio)
            if '.co.mz' in dominio:
                dominio_mz_ocupado = True
        except socket.gaierror:
            tempo = (time.time() - inicio) * 1000
            log("✅", f"DISPONÍVEL ({tempo:.0f}ms)", 2)
        except Exception as e:
            log("⚠️", f"Erro: {e}", 2)
    
    print()
    log("📊", f"Resumo Domínios: {len(dominios_ocupados)}/5 ocupados")
    if dominio_mz_ocupado:
        log("🚨", "ALERTA: Domínio .co.mz OCUPADO! (+60 pontos risco)", 1)
    print()
    
    # ===== BPI =====
    log("📚", "FASE 2: Consultando BPI Local")
    print()
    
    from app import app, IpiRecord
    from sqlalchemy import or_
    from difflib import SequenceMatcher
    
    with app.app_context():
        log("🔍", f"SQL Query: ILIKE '%{termo}%'", 1)
        
        inicio = time.time()
        busca_sql = IpiRecord.query.filter(
            or_(
                IpiRecord.brand_name.ilike(f'%{termo}%'),
                IpiRecord.brand_name.ilike(f'%{termo_limpo}%')
            )
        ).limit(50).all()
        tempo = (time.time() - inicio) * 1000
        
        log("✓", f"Query executada em {tempo:.0f}ms - {len(busca_sql)} resultados", 1)
        
        marcas_similares = []
        max_similaridade = 0
        
        if busca_sql:
            log("🔬", "Calculando similaridade...", 1)
            for registro in busca_sql[:10]:  # Top 10
                nome_bpi = str(registro.brand_name).strip()
                similaridade = SequenceMatcher(
                    None,
                    termo.lower(),
                    nome_bpi.lower()
                ).ratio() * 100
                
                if similaridade >= 60:
                    log("📌", f"{nome_bpi}: {similaridade:.1f}%", 2)
                    marcas_similares.append({
                        'nome': nome_bpi,
                        'similaridade': similaridade,
                        'processo': registro.process_number
                    })
                    max_similaridade = max(max_similaridade, similaridade)
        else:
            log("✓", "Nenhuma marca similar encontrada", 1)
    
    print()
    log("📊", f"Resumo BPI: {len(marcas_similares)} marcas com ≥60% similaridade")
    if max_similaridade >= 90:
        log("🚨", f"ALERTA: Marca IDÊNTICA ({max_similaridade:.0f}%) - +80 pontos risco", 1)
    elif max_similaridade >= 75:
        log("⚠️", f"Marca MUITO SIMILAR ({max_similaridade:.0f}%) - +50 pontos risco", 1)
    elif max_similaridade >= 60:
        log("⚠️", f"Marca similar ({max_similaridade:.0f}%) - +30 pontos risco", 1)
    print()
    
    # ===== REDES SOCIAIS =====
    log("📱", "FASE 3: Verificando Redes Sociais")
    print()
    
    plataformas = {
        'Instagram': f'https://www.instagram.com/{termo_limpo}/',
        'Facebook': f'https://www.facebook.com/{termo_limpo}/',
        'LinkedIn': f'https://www.linkedin.com/company/{termo_limpo}/'
    }
    
    redes_ocupadas = 0
    
    for nome, url in plataformas.items():
        log("🔍", f"Testando: {nome}", 1)
        log("🌐", url, 2)
        
        try:
            inicio = time.time()
            response = requests.get(url, timeout=5, allow_redirects=True)
            tempo = (time.time() - inicio) * 1000
            
            log("📡", f"HTTP {response.status_code} ({tempo:.0f}ms)", 2)
            
            # Análise de conteúdo
            if response.status_code == 200:
                content = response.text.lower()
                
                if nome == 'Instagram':
                    if "sorry, this page isn't available" in content or "page not found" in content:
                        log("✅", "DISPONÍVEL (página não encontrada)", 2)
                    else:
                        log("❌", "OCUPADO (perfil existe)", 2)
                        redes_ocupadas += 1
                
                elif nome == 'Facebook':
                    if 'page not found' in content:
                        log("✅", "DISPONÍVEL", 2)
                    else:
                        log("❌", "OCUPADO", 2)
                        redes_ocupadas += 1
                
                elif nome == 'LinkedIn':
                    if '404' in content or 'page not found' in content:
                        log("✅", "DISPONÍVEL", 2)
                    else:
                        log("❌", "OCUPADO", 2)
                        redes_ocupadas += 1
            
            elif response.status_code == 404:
                log("✅", "DISPONÍVEL (404)", 2)
            else:
                log("⚠️", f"Status indefinido: {response.status_code}", 2)
        
        except requests.exceptions.Timeout:
            log("⏱️", "Timeout (5s)", 2)
        except Exception as e:
            log("❌", f"Erro: {str(e)[:50]}", 2)
        
        print()
    
    log("📊", f"Resumo Redes: {redes_ocupadas}/3 ocupadas")
    if redes_ocupadas > 0:
        log("⚠️", f"+20 pontos risco", 1)
    print()
    
    # ===== CÁLCULO FINAL =====
    log("🧮", "FASE 4: Calculando Risco Total")
    print()
    
    risco_base = 10
    score_dominio = 0
    score_bpi = 0
    score_social = 0
    
    # Domínios
    if dominio_mz_ocupado:
        score_dominio = 60
        log("➕", "Domínio .co.mz ocupado: +60", 1)
    elif dominios_ocupados:
        score_dominio = 20
        log("➕", f"{len(dominios_ocupados)} domínios ocupados: +20", 1)
    
    # BPI
    if max_similaridade >= 90:
        score_bpi = 80
        log("➕", f"BPI similaridade {max_similaridade:.0f}%: +80", 1)
    elif max_similaridade >= 75:
        score_bpi = 50
        log("➕", f"BPI similaridade {max_similaridade:.0f}%: +50", 1)
    elif max_similaridade >= 60:
        score_bpi = 30
        log("➕", f"BPI similaridade {max_similaridade:.0f}%: +30", 1)
    
    # Redes Sociais
    if redes_ocupadas > 0:
        score_social = 20
        log("➕", f"{redes_ocupadas} redes ocupadas: +20", 1)
    
    risco_total = min(100, risco_base + score_dominio + score_bpi + score_social)
    
    print()
    log("🎯", f"RISCO TOTAL: {risco_total}/100", 1)
    
    # Nível
    if risco_total >= 80:
        nivel = "CRÍTICO"
        emoji = "🔴"
    elif risco_total >= 60:
        nivel = "ALTO"
        emoji = "🟠"
    elif risco_total >= 40:
        nivel = "MODERADO"
        emoji = "🟡"
    else:
        nivel = "BAIXO"
        emoji = "🟢"
    
    log(emoji, f"NÍVEL: {nivel}", 1)
    print()
    print("=" * 80)

if __name__ == '__main__':
    termo = sys.argv[1] if len(sys.argv) > 1 else "NIKE"
    verificar_termo_com_logs(termo)
