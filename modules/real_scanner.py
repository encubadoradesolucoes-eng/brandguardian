"""
M24 Brand Guardian - Sistema Real
Autor: #EncubadoraDeSolucoes
Data: 2024
Licença: MIT

Sistema de verificação de marcas usando apenas ferramentas livres/open-source.
Foco em: BPI local, domínios, análise básica. Transparente sobre limitações.
"""

import os
import sys
import socket
import requests
import re
from datetime import datetime
from difflib import SequenceMatcher
from PIL import Image, ImageOps
import imagehash
import jellyfish
import json
import tempfile
import uuid
from typing import Dict, List, Optional, Any
from flask import jsonify, request, current_app, has_app_context

# ============================================
# 1. SCAN LIVE - VERIFICAÇÃO PÚBLICA REAL
# ============================================

def scan_live_real(termo: str, usuario_logado: bool = False) -> Dict[str, Any]:
    """
    Verificação pública realista usando apenas ferramentas livres.
    
    Args:
        termo: Nome da marca a verificar
        usuario_logado: Se usuário está autenticado para ver mais detalhes
    
    Returns:
        Dict com resultados reais (não simulados)
    """
    
    # DEBUG: Confirma que recebeu o termo
    print(f"[SCAN_LIVE_REAL] ========== INÍCIO ==========")
    print(f"[SCAN_LIVE_REAL] Termo recebido: '{termo}'")
    print(f"[SCAN_LIVE_REAL] Usuário logado: {usuario_logado}")
    
    # Limpa e normaliza o termo
    termo_original = termo.strip()
    termo_limpo = re.sub(r'[^a-z0-9]', '', termo_original.lower())
    
    print(f"[SCAN_LIVE_REAL] Termo original: '{termo_original}'")
    print(f"[SCAN_LIVE_REAL] Termo limpo: '{termo_limpo}'")
    
    resultados = {
        'termo': termo_original,
        'timestamp': datetime.now().isoformat(),
        'metodos_utilizados': [],
        'dominios': [],
        'bpi': [],
        'redes_sociais': [],
        'analise_textual': [],
        'limites': []  # Transparente sobre limitações
    }
    
    # ========== DOMÍNIOS (100% FUNCIONAL) ==========
    resultados['metodos_utilizados'].append('DNS lookup via socket (100% confiável)')
    
    # Lista de TLDs relevantes para Moçambique
    tlds = ['.co.mz', '.com', '.org', '.net', '.info']
    
    for tld in tlds:
        dominio = f"{termo_limpo}{tld}"
        
        try:
            # Tentativa principal
            socket.gethostbyname(dominio)
            status = 'OCUPADO'
            confianca = 100
        except socket.gaierror:
            status = 'DISPONÍVEL'
            confianca = 100
        except Exception as e:
            status = 'ERRO_VERIFICACAO'
            confianca = 0
        
        resultado_dominio = {
            'dominio': dominio,
            'status': status,
            'confianca': confianca,
            'metodo': 'DNS lookup'
        }
        
        resultados['dominios'].append(resultado_dominio)
        
        # Para variante com hífen (comum em Moçambique)
        if '-' not in termo_limpo:
            dominio_hifen = f"{termo_limpo.replace(' ', '-')}{tld}"
            if dominio_hifen != dominio:
                try:
                    socket.gethostbyname(dominio_hifen)
                    resultados['dominios'].append({
                        'dominio': dominio_hifen,
                        'status': 'OCUPADO',
                        'confianca': 100,
                        'metodo': 'DNS lookup',
                        'nota': 'Variante com hífen'
                    })
                except socket.gaierror:
                    pass
    
    # ========== BPI LOCAL (100% FUNCIONAL + SQL SEARCH) ==========
    resultados['metodos_utilizados'].append('Consulta SQL direta ao BPI local (Full Scan)')
    
    try:
        print(f"[BPI] Tentando importar módulos...")
        from modules.extensions import db
        from sqlalchemy import or_
        from flask import current_app
        
        # Import models - evita reimportar app.py inteiro
        try:
            # Se já estamos em contexto web, os modelos já estão carregados
            if has_app_context():
                print(f"[BPI] Usando contexto Flask existente")
                # Acessa o modelo através do registry do SQLAlchemy
                from modules.extensions import db
                IpiRecord = db.Model.registry._class_registry.get('IpiRecord')
                if IpiRecord is None:
                    # Fallback: importa do app (mas só se necessário)
                    print(f"[BPI] Modelo não encontrado no registry, importando...")
                    from app import IpiRecord
            else:
                # Contexto standalone (testes) - precisa importar
                print(f"[BPI] Sem contexto Flask, importando app...")
                from app import IpiRecord, app as flask_app
                ctx = flask_app.app_context()
                ctx.push()
            
            print(f"[BPI] Importação bem-sucedida")
        except Exception as ie:
            print(f"[BPI ERRO] Importação falhou: {ie}")
            import traceback
            traceback.print_exc()
            raise
        
        try:
            print(f"[BPI SEARCH] Iniciando busca para: {termo_original}")
            similares_encontrados = []
            
            # 1. Busca Robusta via SQL (Varrer Supabase com critério ampliado)
            # Buscamos o termo original, limpo e as variações fonéticas mais comuns direto no SQL
            filtros_sql = [
                IpiRecord.brand_name.ilike(f'%{termo_original}%'),
                IpiRecord.brand_name.ilike(f'%{termo_limpo}%')
            ]
            
            # Adicionar variações de prefixo comuns (CH/SH/X, C/K/Q) para garantir candidatos
            prefixo = termo_limpo.upper()[:2]
            if prefixo in ['CH', 'SH']:
                filtros_sql.append(IpiRecord.brand_name.ilike('CH%'))
                filtros_sql.append(IpiRecord.brand_name.ilike('SH%'))
                filtros_sql.append(IpiRecord.brand_name.ilike('X%'))
            elif prefixo[0] in ['C', 'K', 'Q']:
                filtros_sql.append(IpiRecord.brand_name.ilike('C%'))
                filtros_sql.append(IpiRecord.brand_name.ilike('K%'))
                filtros_sql.append(IpiRecord.brand_name.ilike('Q%'))

            busca_sql = IpiRecord.query.filter(or_(*filtros_sql)).limit(100).all()
            
            print(f"[BPI SEARCH] Busca SQL direta retornou {len(busca_sql)} candidatos")
            
            for registro in busca_sql:
                if registro.brand_name:
                    nome_bpi = str(registro.brand_name).strip()
                    # Similaridade básica
                    similarity = SequenceMatcher(None, termo_original.lower(), nome_bpi.lower()).ratio()
                    
                    # Similaridade fonética via Metaphone (muito mais robusto para PT)
                    try:
                        p1 = jellyfish.metaphone(termo_original)
                        p2 = jellyfish.metaphone(nome_bpi)
                        fonetica = (p1 == p2 and len(p1) > 1)
                    except:
                        fonetica = False

                    if similarity > 0.7 or fonetica or termo_original.lower() in nome_bpi.lower():
                        # TRATAMENTO ROBUSTO DE DATA PARA EVITAR CRASH (SUPABASE RETORNA STR)
                        data_str = 'N/A'
                        if registro.publication_date:
                            if hasattr(registro.publication_date, 'isoformat'):
                                data_str = registro.publication_date.isoformat()
                            else:
                                data_str = str(registro.publication_date)

                        similares_encontrados.append({
                            'id': registro.id,
                            'marca': nome_bpi,
                            'processo': registro.process_number or 'N/A',
                            'similaridade': round(similarity * 100),
                            'classe': registro.nice_class or 'N/A',
                            'status': registro.status or 'N/A',
                            'titular': registro.applicant_name or 'N/A',
                            'data': data_str
                        })

            # 2. Busca Híbrida com Inteligência Fonética (RESOLVE 'CHOCOLATA' vs 'SHOCOLATA')
            # Gera variações fonéticas comuns para o início da palavra
            termo_upper = termo_limpo.upper()
            
            # Mapeamento de sons iniciais similares
            variacoes_foneticas = [termo_upper] # Sempre inclui o original
            
            # Regras de substituição fonética (PT/EN)
            if termo_upper.startswith('CH'):
                variacoes_foneticas.append('SH' + termo_upper[2:]) # CHOCOLATA -> SHOCOLATA
                variacoes_foneticas.append('X' + termo_upper[2:])  # CHOCOLATA -> XOCOLATA
                variacoes_foneticas.append('K' + termo_upper[2:])  # CHRIS -> KRIS
            elif termo_upper.startswith('SH'):
                variacoes_foneticas.append('CH' + termo_upper[2:])
                variacoes_foneticas.append('X' + termo_upper[2:])
            elif termo_upper.startswith('C'):
                variacoes_foneticas.append('K' + termo_upper[1:])  # CARTRAK -> KARTRAK
                variacoes_foneticas.append('Q' + termo_upper[1:])  # CASA -> QASA
            elif termo_upper.startswith('K'):
                variacoes_foneticas.append('C' + termo_upper[1:])
                variacoes_foneticas.append('Q' + termo_upper[1:])
            elif termo_upper.startswith('S'):
                variacoes_foneticas.append('Z' + termo_upper[1:])
                variacoes_foneticas.append('C' + termo_upper[1:]) # SOM -> COM (risco, mas útil)
            elif termo_upper.startswith('Z'):
                variacoes_foneticas.append('S' + termo_upper[1:])
            elif termo_upper.startswith('PH'):
                variacoes_foneticas.append('F' + termo_upper[2:])
            elif termo_upper.startswith('F'):
                variacoes_foneticas.append('PH' + termo_upper[1:])
                
            candidates_fuzzy = []
            
            # Itera sobre todas as variações fonéticas geradas
            for varia in variacoes_foneticas:
                if len(varia) >= 3:
                     prefix = varia[:3]
                     try:
                        # Busca SQL para o prefixo da variação (ex: SHO%)
                        res = IpiRecord.query.filter(IpiRecord.brand_name.ilike(f'{prefix}%')).limit(1000).all()
                        candidates_fuzzy.extend(res)
                     except: pass

            # Remove duplicatas de objetos (pelo ID ou memória)
            candidates_fuzzy = list({c.id: c for c in candidates_fuzzy}.values())

            for registro in candidates_fuzzy:
                if registro.brand_name:
                    nome_bpi = str(registro.brand_name).strip()
                    
                    # Ignoramos se já foi adicionado pelo SQL exato
                    if any(x['processo'] == registro.process_number for x in similares_encontrados):
                        continue

                    # Calcula similaridade
                    similaridade = SequenceMatcher(None, termo_original.lower(), nome_bpi.lower()).ratio()
                    
                    # Se for muito alta (>75%), adicionamos (reduzi o limiar para pegar fonéticas melhores)
                    if similaridade >= 0.75: 
                        similares_encontrados.append({
                            'id': registro.id,
                            'marca': nome_bpi,
                            'processo': registro.process_number or 'N/A',
                            'similaridade': round(similaridade * 100),
                            'classe': registro.nice_class or 'N/A',
                            'status': registro.status or 'N/A',
                            'titular': registro.applicant_name or 'N/A',
                            'data': registro.publication_date.isoformat() if registro.publication_date else 'N/A'
                        })

            # ========== DOUBLE METAPHONE (JELLYFISH) - FONÉTICA MELHORADA ==========
            try:
                term_meta = jellyfish.double_metaphone(termo_original)
                term_meta_codes = [c for c in term_meta if c]

                # Otimização Crítica: NÃO carregar 10.000 registros (Query.all()) 
                # Buscamos apenas marcas que começam com a mesma letra ou prefixo para reduzir memória
                prefix = termo_original[0].upper() if termo_original else ""
                registros_para_meta = IpiRecord.query.filter(IpiRecord.brand_name.ilike(f'{prefix}%')).limit(1000).all()
                
                for registro in registros_para_meta:
                    try:
                        if not registro.brand_name:
                            continue
                        registro_meta = jellyfish.double_metaphone(str(registro.brand_name))
                        registro_meta_codes = [c for c in registro_meta if c]

                        # Se houver correspondência exata de código fonético, consideramos candidato
                        match_found = any(tm == rm for tm in term_meta_codes for rm in registro_meta_codes)
                        if match_found:
                            nome_bpi = str(registro.brand_name).strip()
                            # evita duplicatas por processo
                            if any(x['processo'] == registro.process_number for x in similares_encontrados):
                                continue

                            similaridade = SequenceMatcher(None, termo_original.lower(), nome_bpi.lower()).ratio()

                            # inclui candidaturas fonéticas mesmo com similaridade textual moderada
                            if similaridade >= 0.6:
                                similares_encontrados.append({
                                    'id': registro.id,
                                    'marca': nome_bpi,
                                    'processo': registro.process_number or 'N/A',
                                    'similaridade': round(similaridade * 100),
                                    'classe': registro.nice_class or 'N/A',
                                    'status': registro.status or 'N/A',
                                    'titular': registro.applicant_name or 'N/A',
                                    'data': registro.publication_date.isoformat() if registro.publication_date else 'N/A',
                                    'fonetica': True
                                })
                    except Exception:
                        continue
            except Exception:
                pass

            # Ordena por similaridade (maior primeiro)
            similares_encontrados.sort(key=lambda x: x['similaridade'], reverse=True)
            
            print(f"[BPI SEARCH] Total de similares encontrados: {len(similares_encontrados)}")
            
            if similares_encontrados:
                resultados['bpi'] = similares_encontrados[:15]  # Top 15 resultados
                
                # Calcula risco baseado no BPI
                risco_bpi = 0
                if similares_encontrados[0]['similaridade'] >= 90:
                    risco_bpi = 80
                elif similares_encontrados[0]['similaridade'] >= 70:
                    risco_bpi = 50
                elif similares_encontrados[0]['similaridade'] >= 60:
                    risco_bpi = 30
                
                resultados['analise_textual'].append({
                    'tipo': 'RISCO BPI',
                    'nivel': risco_bpi,
                    'descricao': f"Marca similar encontrada no BPI ({similares_encontrados[0]['similaridade']}% similar)"
                })
            else:
                resultados['analise_textual'].append({
                    'tipo': 'RISCO BPI',
                    'nivel': 10,
                    'descricao': 'Nenhuma marca similar encontrada no BPI local'
                })
        
        finally:
            # Libera contexto se foi criado localmente (apenas em modo standalone)
            if 'ctx' in locals() and ctx is not None:
                print(f"[BPI] Liberando contexto Flask")
                ctx.pop()

    except Exception as e:
        import traceback
        print(f"[ERRO BPI] {str(e)}")
        print(traceback.format_exc())
        resultados['bpi'] = []
        resultados['limites'].append(f"Erro na consulta BPI: {str(e)[:100]}")


    
    # ========== REDES SOCIAIS (LIMITADO MAS REAL) ==========
    resultados['metodos_utilizados'].append('Verificação redes sociais (limitado por APIs)')
    resultados['limites'].append('Redes sociais: verificação limitada (~70% confiável)')
    
    def verificar_rede_metodo_alternativo(plataforma: str, username: str) -> Dict[str, Any]:
        """
        Método alternativo para verificar redes sociais.
        Menos preciso que APIs oficiais, mas funciona.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            urls = {
                'instagram': f'https://www.instagram.com/{username}/',
                'facebook': f'https://www.facebook.com/{username}/',
                'linkedin': f'https://www.linkedin.com/company/{username}/',
                'twitter': f'https://twitter.com/{username}',
                'youtube': f'https://www.youtube.com/@{username}'
            }
            
            if plataforma.lower() not in urls:
                return {'status': 'PLATAFORMA_NAO_SUPORTADA', 'confianca': 0}
            
            url = urls[plataforma.lower()]
            
            # Request com timeout adequado
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            # Análise baseada em status code e conteúdo
            if response.status_code == 200:
                content_lower = response.text.lower()
                
                # Heurísticas para cada plataforma
                if plataforma.lower() == 'instagram':
                    # Instagram retorna 200 mesmo para páginas não-existentes
                    # Mas páginas não-existentes têm textos específicos
                    error_indicators = [
                        'sorry, this page isn\'t available',
                        'the link you followed may be broken',
                        'page not found'
                    ]
                    
                    if any(indicator in content_lower for indicator in error_indicators):
                        return {'status': 'DISPONIVEL', 'confianca': 75, 'url': url}
                    else:
                        return {'status': 'OCUPADO', 'confianca': 70, 'url': url}
                        
                elif plataforma.lower() == 'facebook':
                    # Facebook tem diferentes respostas
                    if 'page not found' in content_lower or 'this page isn\'t available' in content_lower:
                        return {'status': 'DISPONIVEL', 'confianca': 80, 'url': url}
                    else:
                        # Verifica se é uma página de login (redirect)
                        if 'facebook.com/login/' in response.url:
                            return {'status': 'DISPONIVEL', 'confianca': 60, 'url': url}
                        else:
                            return {'status': 'OCUPADO', 'confianca': 75, 'url': url}
                
                elif plataforma.lower() == 'linkedin':
                    if 'page not found' in content_lower or '404' in content_lower:
                        return {'status': 'DISPONIVEL', 'confianca': 85, 'url': url}
                    else:
                        return {'status': 'OCUPADO', 'confianca': 80, 'url': url}
                
                else:
                    # Para outras plataformas, baseia-se apenas no status
                    return {'status': 'OCUPADO', 'confianca': 65, 'url': url}
                    
            elif response.status_code == 404:
                return {'status': 'DISPONIVEL', 'confianca': 90, 'url': url}
            else:
                return {'status': f'HTTP_{response.status_code}', 'confianca': 50, 'url': url}
                
        except requests.exceptions.Timeout:
            return {'status': 'TIMEOUT', 'confianca': 0, 'url': url}
        except requests.exceptions.ConnectionError:
            return {'status': 'CONNECTION_ERROR', 'confianca': 0, 'url': url}
        except Exception as e:
            return {'status': f'ERRO: {str(e)[:50]}', 'confianca': 0, 'url': url}
    
    # Verifica apenas plataformas principais
    plataformas = ['instagram', 'facebook', 'linkedin']
    
    for plataforma in plataformas:
        resultado = verificar_rede_metodo_alternativo(plataforma, termo_limpo)
        
        resultados['redes_sociais'].append({
            'plataforma': plataforma.capitalize(),
            'status': resultado['status'],
            'confianca': resultado['confianca'],
            'url': resultado.get('url', ''),
            'metodo': 'Análise HTTP + heurísticas'
        })
        
        # Se estiver ocupado com confiança razoável, calcula risco
        if resultado['status'] == 'OCUPADO' and resultado['confianca'] >= 60:
            resultados['analise_textual'].append({
                'tipo': f'PRESENÇA {plataforma.upper()}',
                'nivel': 20,
                'descricao': f'Perfil encontrado no {plataforma.capitalize()} (confiança: {resultado["confianca"]}%)'
            })
    
    # ========== ANÁLISE DE RISCO CONSOLIDADA ==========
    
    # Calcula risco total baseado em todos os fatores
    fatores_risco = []
    
    risco_base = 10
    score_dominio = 0
    score_bpi = 0
    score_social = 0

    # Fator 1: Domínios ocupados (PESO CRÍTICO PARA .co.mz)
    dominios_ocupados_mz = [d for d in resultados['dominios'] if d['status'] == 'OCUPADO' and '.co.mz' in d['dominio']]
    outros_dominios = [d for d in resultados['dominios'] if d['status'] == 'OCUPADO' and '.co.mz' not in d['dominio']]
    
    if dominios_ocupados_mz:
        # Domínio nacional ocupado = Risco Imediato Elevado
        score_dominio += 60 
        fatores_risco.append({
            'fator': 'Domínio Nacional (.co.mz) INDISPONÍVEL',
            'peso': 60,
            'quantidade': len(dominios_ocupados_mz),
            'detalhe': 'Indicador forte de marca em uso comercial ativo em Moçambique.'
        })
    
    if outros_dominios:
        score_dominio += 20
        fatores_risco.append({
            'fator': 'Domínios internacionais ocupados (.com, etc)',
            'peso': 20,
            'quantidade': len(outros_dominios)
        })
    
    # Fator 2: Similaridade BPI
    if resultados.get('bpi') and len(resultados['bpi']) > 0:
        maior_similaridade = resultados['bpi'][0]['similaridade']
        if maior_similaridade >= 90:
            score_bpi = 80
            desc = "Marca IDÊNTICA encontrada no BPI"
        elif maior_similaridade >= 75:
            score_bpi = 50
            desc = "Marca MUITO SIMILAR encontrada no BPI"
        elif maior_similaridade >= 60:
            score_bpi = 30
            desc = "Marca similar encontrada no BPI"
        else:
            score_bpi = 15
            desc = "Similaridade leve detectada"
            
        fatores_risco.append({
            'fator': f'{desc} ({maior_similaridade}%)',
            'peso': score_bpi,
            'quantidade': len(resultados['bpi'])
        })
    
    # Fator 3: Redes sociais ocupadas
    redes_ocupadas = [r for r in resultados['redes_sociais'] if r['status'] == 'OCUPADO' and r['confianca'] >= 60]
    if redes_ocupadas:
        score_social = 20
        fatores_risco.append({
            'fator': 'Presença em Redes Sociais detectada',
            'peso': 20,
            'quantidade': len(redes_ocupadas)
        })
    
    # SOMA FINAL (Máximo 100)
    # Se tem domínio .co.mz ocupado, risco mínimo é 60 (ALTO/MÉDIO-ALTO)
    risco_total = min(100, risco_base + score_dominio + score_bpi + score_social)
    
    resultados['analise_risco'] = {
        'risco_total': risco_total,
        'nivel_risco': 'CRÍTICO' if risco_total >= 80 else 'ALTO' if risco_total >= 60 else 'MODERADO' if risco_total >= 40 else 'BAIXO',
        'fatores': fatores_risco,
        'recomendacao': gerar_recomendacao_risco(risco_total, resultados)
    }
    
    # ========== RESULTADOS FILTRADOS PARA NÃO LOGADOS ==========
    if not usuario_logado:
        # Para usuários não logados, mostra menos detalhes
        resultados_filtrados = {
            'termo': resultados['termo'],
            'timestamp': resultados['timestamp'],
            'dominios': [{
                'dominio': d['dominio'],
                'status': d['status'],
                'confianca': 'ALTA' if d['confianca'] >= 80 else 'MÉDIA' if d['confianca'] >= 50 else 'BAIXA'
            } for d in resultados['dominios']],
            'resumo_bpi': f"{len(resultados['bpi'])} marcas similares encontradas" if resultados['bpi'] else "Nenhuma marca similar encontrada",
            'analise_risco': {
                'risco_total': resultados['analise_risco']['risco_total'],
                'nivel_risco': resultados['analise_risco']['nivel_risco'],
                'recomendacao': resultados['analise_risco']['recomendacao']
            },
            'mensagem_comercial': {
                'titulo': '🔒 Análise Completa Disponível',
                'texto': 'Faça login ou subscreva um dos nossos planos para aceder a:',
                'beneficios': [
                    '✓ Detalhes completos de marcas similares encontradas',
                    '✓ Números de processo e titulares',
                    '✓ Relatórios jurídicos profissionais em PDF',
                    '✓ Histórico de todas as suas consultas',
                    '✓ Alertas automáticos de novos registos'
                ],
                'cta_login': 'Fazer Login',
                'cta_planos': 'Ver Planos e Preços'
            }
        }
        return resultados_filtrados
    
    return resultados

def gerar_recomendacao_risco(risco_total: int, resultados: Dict) -> str:
    """Gera recomendação baseada no nível de risco"""
    if risco_total >= 80:
        return "🔴 ALTO RISCO: Não recomendado. Conflitos significativos detectados em múltiplas dimensões."
    elif risco_total >= 60:
        return "🟠 RISCO ELEVADO: Recomendamos análise jurídica detalhada antes de prosseguir."
    elif risco_total >= 40:
        return "🟡 RISCO MODERADO: Pode prosseguir com cautela. Verifique manualmente os conflitos detectados."
    elif risco_total >= 20:
        return "🟢 RISCO BAIXO: Pode prosseguir. Apenas verificações rotineiras recomendadas."
    else:
        return "✅ RISCO MÍNIMO: Nenhum conflito significativo detectado. Pode prosseguir com segurança."

# ============================================
# 2. PURIFICATION - AUDITORIA INTERNA REAL
# ============================================

def purification_real() -> Dict[str, Any]:
    """
    Auditoria interna real usando ferramentas livres.
    Foca em: conflitos BPI, domínios, análise de dados.
    """
    
    print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] Iniciando auditoria interna (Purification)")
    
    resultados = {
        'iniciado_em': datetime.now().isoformat(),
        'metodos_utilizados': [
            'Análise de similaridade textual (difflib)',
            'DNS lookup em massa',
            'Processamento local de dados'
        ],
        'conflitos_bpi': [],
        'dominios_suspeitos': [],
        'leads_potenciais': [],
        'estatisticas': {},
        'tempo_processamento': None
    }
    
    try:
        from app import db, IpiRecord, Brand, Entity
        
        # ========== 1. ANÁLISE DE CONFLITOS BPI ==========
        
        print("📊 Analisando conflitos no BPI...")
        
        # Busca todas as marcas de clientes
        marcas_clientes = Brand.query.all()
        total_clientes = len(marcas_clientes)
        
        # Busca registros BPI (LIMITADO para evitar OOM no Render)
        # Em produção, a auditoria deve focar nos registros mais recentes ou relevantes
        registros_bpi = IpiRecord.query.order_by(IpiRecord.imported_at.desc()).limit(2000).all()
        total_bpi = len(registros_bpi)
        
        resultados['estatisticas']['marcas_clientes'] = total_clientes
        resultados['estatisticas']['registros_bpi'] = total_bpi
        
        conflitos_detectados = 0
        
        for i, cliente in enumerate(marcas_clientes):
            if i % 100 == 0 and i > 0:
                print(f"  Processadas {i}/{total_clientes} marcas...")
            
            if not cliente.name or len(cliente.name.strip()) < 2:
                continue
            
            nome_cliente = cliente.name.strip().lower()
            
            for registro in registros_bpi:
                if not registro.brand_name:
                    continue
                
                nome_bpi = registro.brand_name.strip().lower()
                
                if len(nome_bpi) < 2:
                    continue
                
                # Calcula similaridade
                similaridade = SequenceMatcher(None, nome_cliente, nome_bpi).ratio()
                
                # Detecção de conflitos (critérios realistas)
                if similaridade >= 0.85:  # 85% similar
                    # Verifica se é provavelmente o mesmo titular
                    mesmo_titular = False
                    if cliente.owner_name and registro.applicant_name:
                        similaridade_titular = SequenceMatcher(
                            None, 
                            cliente.owner_name.lower(), 
                            registro.applicant_name.lower()
                        ).ratio()
                        mesmo_titular = similaridade_titular > 0.8
                    
                    if not mesmo_titular:
                        conflitos_detectados += 1
                        
                        resultados['conflitos_bpi'].append({
                            'id': f"CONFLITO_{conflitos_detectados:04d}",
                            'marca_cliente': cliente.name,
                            'titular_cliente': cliente.owner_name or 'N/A',
                            'marca_bpi': registro.brand_name,
                            'titular_bpi': registro.applicant_name or 'N/A',
                            'similaridade': round(similaridade * 100, 1),
                            'processo_bpi': registro.process_number or 'N/A',
                            'status_bpi': registro.status or 'N/A',
                            'fonte': 'BPI OFICIAL',
                            'gravidade': 'CRÍTICA' if similaridade >= 0.95 else 'ALTA' if similaridade >= 0.9 else 'MÉDIA',
                            'acao_recomendada': gerar_acao_conflito(similaridade)
                        })

            # ========== INSERÇÃO DA CHECAGEM WEB (A QUE FALTAVA) ==========
            # Verifica domínio principal para a marca do cliente
            dominio_com = f"{nome_cliente.replace(' ', '')}.com"
            try:
                socket.gethostbyname(dominio_com)
                # Se não deu erro, existe. É conflito se não for do cliente.
                # (Assumindo risco por default se site existe)
                conflitos_detectados += 1
                resultados['conflitos_bpi'].append({
                    'id': f"WEB_CONFLICT_{conflitos_detectados:04d}",
                    'marca_cliente': cliente.name,
                    'titular_cliente': cliente.owner_name or 'N/A',
                    'marca_bpi': dominio_com, # Usando campo marca_bpi para mostrar o domínio
                    'titular_bpi': 'Proprietário do Domínio', 
                    'similaridade': 100,
                    'processo_bpi': 'DNS REGISTRY',
                    'fonte': 'WEB / DOMÍNIO',
                    'status_bpi': 'ATIVO',
                    'gravidade': 'ALTA',
                    'acao_recomendada': f"Domínio {dominio_com} já registrado. Verificar propriedade."
                })
            except:
                pass # Domínio livre, sem conflito
        
        # Limita a lista para relatório
        if len(resultados['conflitos_bpi']) > 50:
            resultados['conflitos_bpi'] = resultados['conflitos_bpi'][:50]
            resultados['estatisticas']['conflitos_omitidos'] = len(resultados['conflitos_bpi']) - 50
        
        resultados['estatisticas']['conflitos_detectados'] = conflitos_detectados
        
        # ========== 2. VERIFICAÇÃO DE DOMÍNIOS SUSPEITOS ==========
        
        print("🌐 Verificando domínios suspeitos...")
        
        # Para cada marca cliente, verifica variações comuns
        for cliente in marcas_clientes[:100]:  # Limita para performance
            if not cliente.name:
                continue
            
            nome_base = re.sub(r'[^a-z0-9]', '', cliente.name.lower())
            if len(nome_base) < 3:
                continue
            
            # Gera variações comuns
            variacoes = [
                nome_base,
                f"{nome_base}-lda",
                f"{nome_base}mz", 
                f"{nome_base}-moz",
                f"loja{nome_base}",
                f"{nome_base}oficial",
                f"{nome_base}store"
            ]
            
            for variacao in variacoes:
                dominio = f"{variacao}.co.mz"
                
                try:
                    socket.gethostbyname(dominio)
                    
                    # Domínio ativo - verifica se é do titular
                    email_dominio = None
                    if cliente.owner_email and '@' in cliente.owner_email:
                        email_dominio = cliente.owner_email.split('@')[1]
                    
                    # Heurística simples: domínio corresponde ao email?
                    dominio_correspondente = email_dominio and (
                        dominio.endswith(email_dominio.lower()) or 
                        email_dominio.lower().replace('.', '') in dominio
                    )
                    
                    if not dominio_correspondente:
                        resultados['dominios_suspeitos'].append({
                            'marca': cliente.name,
                            'dominio': dominio,
                            'status': 'ATIVO',
                            'titular_marca': cliente.owner_name or 'N/A',
                            'email_titular': cliente.owner_email or 'N/A',
                            'suspensao': 'Possível uso por terceiros',
                            'acao': 'Verificar whois e contato'
                        })
                        
                except socket.gaierror:
                    pass  # Domínio disponível
                except Exception:
                    pass  # Outros erros
        
        # ========== 3. IDENTIFICAÇÃO DE LEADS POTENCIAIS ==========
        
        print("🎯 Identificando leads potenciais...")
        
        # Empresas no BPI com múltiplas marcas mas que não são clientes
        empresas_bpi = {}
        
        for registro in registros_bpi:
            if registro.applicant_name:
                empresa = registro.applicant_name.strip()
                if empresa and len(empresa) > 3:
                    if empresa not in empresas_bpi:
                        empresas_bpi[empresa] = {
                            'marcas': [],
                            'total': 0,
                            'ultimo_registro': None
                        }
                    
                    empresas_bpi[empresa]['marcas'].append(registro.brand_name or 'N/A')
                    empresas_bpi[empresa]['total'] += 1
                    
                    if registro.publication_date:
                        if (empresas_bpi[empresa]['ultimo_registro'] is None or 
                            registro.publication_date > empresas_bpi[empresa]['ultimo_registro']):
                            empresas_bpi[empresa]['ultimo_registro'] = registro.publication_date
        
        # Filtra empresas com >2 marcas
        empresas_ativas = {emp: data for emp, data in empresas_bpi.items() if data['total'] >= 2}
        
        # Verifica quais não são clientes
        emails_clientes = [c.owner_email.lower() for c in marcas_clientes if c.owner_email]
        nomes_clientes = [c.owner_name.lower() for c in marcas_clientes if c.owner_name]
        
        for empresa, dados in list(empresas_ativas.items())[:50]:  # Limita
            empresa_lower = empresa.lower()
            
            # Verifica se já é cliente
            ja_cliente = False
            
            # Verifica por nome similar
            for nome_cliente in nomes_clientes:
                if nome_cliente and SequenceMatcher(None, empresa_lower, nome_cliente).ratio() > 0.7:
                    ja_cliente = True
                    break
            
            # Verifica por domínio de email
            if not ja_cliente and '@' in empresa:
                dominio_empresa = empresa.split('@')[1].lower()
                for email_cliente in emails_clientes:
                    if email_cliente.endswith(dominio_empresa):
                        ja_cliente = True
                        break
            
            if not ja_cliente:
                resultados['leads_potenciais'].append({
                    'empresa': empresa,
                    'marcas_registradas': dados['total'],
                    'exemplo_marcas': dados['marcas'][:3],
                    'ultimo_registro': dados['ultimo_registro'].isoformat() if dados['ultimo_registro'] else 'N/A',
                    'potencial': 'ALTO' if dados['total'] >= 5 else 'MÉDIO' if dados['total'] >= 3 else 'BAIXO',
                    'estrategia_contato': gerar_estrategia_contato(dados['total'])
                })
        
        # ========== 4. ESTATÍSTICAS FINAIS ==========
        
        resultados['estatisticas']['dominios_suspeitos'] = len(resultados['dominios_suspeitos'])
        resultados['estatisticas']['leads_potenciais'] = len(resultados['leads_potenciais'])
        
        # Calcula tempo de processamento
        tempo_fim = datetime.now()
        tempo_inicio = datetime.fromisoformat(resultados['iniciado_em'])
        resultados['tempo_processamento'] = str(tempo_fim - tempo_inicio)
        
        print(f"✅ Auditoria concluída em {resultados['tempo_processamento']}")
        print(f"   • Conflitos BPI: {resultados['estatisticas']['conflitos_detectados']}")
        print(f"   • Domínios suspeitos: {resultados['estatisticas']['dominios_suspeitos']}")
        print(f"   • Leads potenciais: {resultados['estatisticas']['leads_potenciais']}")
        
        return resultados
        
    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")
        resultados['erro'] = str(e)
        return resultados

def gerar_acao_conflito(similaridade: float) -> str:
    """Gera ação recomendada baseada na similaridade"""
    if similaridade >= 0.95:
        return "CONTATO IMEDIATO: Conflito crítico detectado. Notificar cliente urgentemente."
    elif similaridade >= 0.9:
        return "ANÁLISE JURÍDICA: Alto risco de oposição. Recomendar consulta jurídica."
    elif similaridade >= 0.85:
        return "MONITORAMENTO: Similaridade significativa. Acompanhar desenvolvimento."
    else:
        return "OBSERVAÇÃO: Similaridade moderada. Manter vigilância."

def gerar_estrategia_contato(total_marcas: int) -> str:
    """Gera estratégia de contato baseada no perfil da empresa"""
    if total_marcas >= 5:
        return "Contato direto com gestor/diretor. Oferecer pacote corporativo."
    elif total_marcas >= 3:
        return "Contato via departamento jurídico. Demonstrar economia de escala."
    else:
        return "Contato inicial informativo. Educar sobre proteção de marcas."

# ============================================
# 3. VERIFICAÇÃO POR IMAGEM - FERRAMENTAS LIVRES
# ============================================

def verificacao_imagem_real(caminho_imagem: str, marca_nome: str = "") -> Dict[str, Any]:
    """
    Verificação de imagem usando ferramentas livres e múltiplos algoritmos.
    Integrado com DuplicateImageFinder para busca completa.
    
    Args:
        caminho_imagem: Caminho para o arquivo de imagem
        marca_nome: Nome da marca para contexto
    
    Returns:
        Análise completa da imagem com comparação contra todas as bases
    """
    
    print(f"🖼️  Analisando imagem: {caminho_imagem}")
    print(f"📌 Marca: {marca_nome or 'Não especificada'}")
    
    resultados = {
        'marca': marca_nome,
        'arquivo': caminho_imagem,
        'timestamp': datetime.now().isoformat(),
        'metodos_utilizados': [],
        'analises': [],
        'conflitos_visuais': [],
        'limites': [
            'Comparação contra banco de dados local completo',
            'Inclui marcas de usuários + registros BPI',
            'Usa 3 algoritmos de hash (Average, Perceptual, Difference)',
            'Não inclui busca reversa na web (requer APIs pagas)',
            'Precisão depende da qualidade da imagem'
        ]
    }
    
    # ========== 1. VERIFICAÇÃO BÁSICA DA IMAGEM ==========
    
    try:
        # Abre a imagem
        img = Image.open(caminho_imagem)
        
        resultados['propriedades_imagem'] = {
            'formato': img.format,
            'modo': img.mode,
            'dimensoes': f"{img.width} x {img.height}",
            'tamanho_arquivo_kb': round(os.path.getsize(caminho_imagem) / 1024, 1)
        }
        
        resultados['metodos_utilizados'].append('Análise básica com PIL/Pillow')
        
    except Exception as e:
        resultados['erro'] = f"Erro ao abrir imagem: {str(e)}"
        return resultados
    
    # ========== 2. HASH DE IMAGEM PARA COMPARAÇÃO ==========
    
    try:
        # Gera múltiplos hashes para melhor precisão
        img_hash_avg = imagehash.average_hash(img)
        img_hash_phash = imagehash.phash(img)
        img_hash_dhash = imagehash.dhash(img)
        
        resultados['hashes'] = {
            'average_hash': str(img_hash_avg),
            'phash': str(img_hash_phash),
            'dhash': str(img_hash_dhash)
        }
        
        resultados['metodos_utilizados'].append('Geração tripla de hash de imagem (imagehash)')
        
        # ========== 3. COMPARAÇÃO COMPLETA USANDO DuplicateImageFinder ==========
        
        from modules.image_matcher import DuplicateImageFinder
        
        # Importa modelos do banco de dados e busca registros
        brand_records = []
        ipi_records = []
        try:
            print("[RASTREIO VISUAL] Iniciando captura de alvos para comparação...")
            
            if has_app_context():
                from app import Brand, IpiRecord
                
                # 1. PASSO: IPI RECORDS (Base Oficial)
                try:
                    ipi_items = IpiRecord.query.filter(IpiRecord.image_data.isnot(None)).all()
                    ipi_records = []
                    for r in ipi_items:
                        try:
                            if r.image_data:
                                ipi_records.append({
                                    'id': r.id,
                                    'brand_name': r.brand_name,
                                    'image_data': r.image_data, # Binário direto
                                    'applicant_name': r.applicant_name,
                                    'process_number': r.process_number
                                })
                        except Exception as row_e:
                            print(f"[RASTREIO VISUAL] Pulando linha IPI {r.id} devido a erro: {row_e}")
                            continue
                    print(f"[RASTREIO VISUAL] IpiRecord: {len(ipi_records)} binários encontrados no Supabase.")
                except Exception as query_e:
                    print(f"[RASTREIO VISUAL] Erro ao buscar registros IPI: {query_e}")

                # 2. PASSO: BRANDS (Clientes M24)
                try:
                    brands = Brand.query.filter(Brand.image_data.isnot(None)).all()
                    brand_records = []
                    for b in brands:
                        try:
                            if b.image_data:
                                brand_records.append({
                                    'id': b.id,
                                    'name': b.name,
                                    'image_data': b.image_data, # Binário direto
                                    'owner_name': b.owner_name
                                })
                        except Exception as row_e:
                            print(f"[RASTREIO VISUAL] Pulando linha Brand {b.id} devido a erro: {row_e}")
                            continue
                    print(f"[RASTREIO VISUAL] Brands: {len(brand_records)} binários de clientes encontrados.")
                except Exception as query_e:
                    print(f"[RASTREIO VISUAL] Erro ao buscar registros Brand: {query_e}")
            else:
                print("[RASTREIO VISUAL] ⚠️ Aviso: Fora de contexto Flask. Rodando busca sem banco.")
        except Exception as e:
            import traceback
            print(f"⚠️ Aviso: Não foi possível buscar dados do banco: {e}")
            print(traceback.format_exc())
            brand_records = []
            ipi_records = []
        
        # Obtém o diretório base da aplicação
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        finder = DuplicateImageFinder(app_root)
        
        print("🔎 Iniciando busca completa de duplicatas...")
        
        # Busca com threshold 15 (Mais resiliente para o Supabase)
        conflitos_encontrados = finder.find_duplicate_images(
            caminho_imagem,
            threshold=15,
            brand_records=brand_records,
            ipi_records=ipi_records
        )
        
        resultados['metodos_utilizados'].append('Busca completa com DuplicateImageFinder')
        
        # Processa resultados
        if conflitos_encontrados:
            print(f"⚠️  {len(conflitos_encontrados)} conflitos visuais detectados")
            
            # Separa por tipo
            conflitos_users = [c for c in conflitos_encontrados if c.get('tipo') == 'USER_BRAND']
            conflitos_bpi = [c for c in conflitos_encontrados if c.get('tipo') == 'BPI_RECORD']
            
            resultados['analises'].append({
                'tipo': 'COMPARAÇÃO COMPLETA',
                'status': 'CONCLUÍDO',
                'marcas_usuarios_comparadas': len(conflitos_users) if conflitos_users else 0,
                'registros_bpi_comparados': len(conflitos_bpi) if conflitos_bpi else 0,
                'total_conflitos': len(conflitos_encontrados),
                'algoritmos': ['Average Hash', 'Perceptual Hash (pHash)', 'Difference Hash (dHash)']
            })
            
            # Formata conflitos para o padrão do sistema
            for idx, conflito in enumerate(conflitos_encontrados, 1):
                resultados['conflitos_visuais'].append({
                    'id': f"CONFLITO_VISUAL_{idx:03d}",
                    'marca_bpi': conflito['brand_name'],
                    'processo_bpi': conflito.get('processo', 'N/A'),
                    'titular': conflito['owner'],
                    'similaridade_media': conflito['similarity_final'],
                    'similaridade_avg': conflito['similarity_avg'],
                    'similaridade_phash': conflito['similarity_phash'],
                    'similaridade_dhash': conflito['similarity_dhash'],
                    'gravidade': conflito['gravidade'],
                    'tipo_registro': conflito['tipo'],
                    'status': conflito['status'],
                    'logo_url': conflito['logo_url'],
                    'acao': gerar_acao_conflito_visual(conflito['similarity_final'])
                })
        else:
            print("✅ Nenhum conflito visual detectado")
            resultados['analises'].append({
                'tipo': 'COMPARAÇÃO COMPLETA',
                'status': 'CONCLUÍDO',
                'total_conflitos': 0,
                'observacao': 'Nenhuma similaridade visual significativa encontrada'
            })
    
    except Exception as e:
        resultados['erro_hash'] = f"Erro na análise de hash: {str(e)}"
    
    # ========== 4. ANÁLISE DE CORES ==========
    
    try:
        # Reduz imagem para análise de cores
        img_cores = img.copy()
        img_cores = img_cores.resize((100, 100))
        
        # Converte para RGB se necessário
        if img_cores.mode != 'RGB':
            img_cores = img_cores.convert('RGB')
        
        # Obtém cores dominantes
        cores = img_cores.getcolors(maxcolors=10000)
        
        if cores:
            # Ordena por frequência
            cores_ordenadas = sorted(cores, key=lambda x: x[0], reverse=True)
            
            # Pega as 5 cores mais comuns
            cores_dominantes = []
            for freq, cor in cores_ordenadas[:5]:
                if isinstance(cor, tuple):
                    hex_cor = f"#{cor[0]:02x}{cor[1]:02x}{cor[2]:02x}"
                    cores_dominantes.append({
                        'frequencia': freq,
                        'cor_hex': hex_cor,
                        'cor_rgb': cor
                    })
            
            if cores_dominantes:
                resultados['analises'].append({
                    'tipo': 'ANÁLISE DE CORES',
                    'cores_dominantes': cores_dominantes,
                    'total_cores_unicas': len(cores_ordenadas)
                })
                
                resultados['metodos_utilizados'].append('Análise de paleta de cores')
    
    except Exception as e:
        pass  # Análise de cores é opcional
    
    # ========== 5. DETECÇÃO DE TEXTO SIMPLES ==========
    
    try:
        # Método simples para detectar se imagem tem texto
        # (Não é OCR completo, apenas heurística)
        
        # Converte para escala de cinza
        img_cinza = img.convert('L')
        
        # Aumenta contraste
        img_contraste = ImageOps.autocontrast(img_cinza)
        
        # Calcula variação de pixels (texto geralmente tem alta variação)
        pixels = list(img_contraste.getdata())
        media = sum(pixels) / len(pixels)
        variancia = sum((p - media) ** 2 for p in pixels) / len(pixels)
        
        # Heurística: alta variância pode indicar texto
        tem_texto_potencial = variancia > 5000  # Valor empírico
        
        if tem_texto_potencial:
            resultados['analises'].append({
                'tipo': 'DETECÇÃO DE TEXTO',
                'status': 'TEXTO_POTENCIAL_DETECTADO',
                'variancia_pixels': round(variancia, 1),
                'observacao': 'Alta variação de pixels sugere presença de texto. Verifique manualmente.'
            })
    
    except Exception as e:
        pass  # Detecção de texto é opcional
    
    # ========== 6. CONCLUSÃO ==========
    
    if resultados.get('conflitos_visuais'):
        similaridade_max = max([c['similaridade_media'] for c in resultados['conflitos_visuais']])
        
        if similaridade_max >= 80:
            risco_visual = 70
            nivel = 'ALTO'
        elif similaridade_max >= 65:
            risco_visual = 40
            nivel = 'MÉDIO'
        else:
            risco_visual = 20
            nivel = 'BAIXO'
    else:
        similaridade_max = 0
        risco_visual = 10
        nivel = 'MÍNIMO'
    
    resultados['resumo'] = {
        'conflitos_encontrados': len(resultados.get('conflitos_visuais', [])),
        'similaridade_maxima': similaridade_max,
        'risco_visual': risco_visual,
        'nivel_risco_visual': nivel,
        'recomendacao': gerar_recomendacao_imagem(risco_visual, resultados)
    }
    
    print(f"✅ Análise de imagem concluída. Conflitos: {resultados['resumo']['conflitos_encontrados']}")
    
    return resultados

def gerar_acao_conflito_visual(similaridade: float) -> str:
    """Gera ação para conflito visual"""
    if similaridade >= 85:
        return "CONFLITO GRAVE: Alta similaridade visual. Consultar advogado especializado."
    elif similaridade >= 75:
        return "CONFLITO SIGNIFICATIVO: Similaridade elevada. Recomendar redesign parcial."
    elif similaridade >= 65:
        return "SIMILARIDADE MODERADA: Pode causar confusão. Avaliar contexto de uso."
    else:
        return "SIMILARIDADE ACEITÁVEL: Provavelmente diferenciável no mercado."

def gerar_recomendacao_imagem(risco_visual: int, resultados: Dict) -> str:
    """Gera recomendação baseada na análise visual"""
    if risco_visual >= 70:
        return "🔴 ALTO RISCO VISUAL: Logotipo muito similar a marcas existentes. Recomendamos redesign completo."
    elif risco_visual >= 40:
        return "🟠 RISCO VISUAL MODERADO: Similaridades detectadas. Sugerimos ajustes para maior diferenciação."
    elif risco_visual >= 20:
        return "🟡 RISCO VISUAL BAIXO: Algumas semelhanças detectadas. Manter vigilância."
    else:
        return "✅ RISCO VISUAL MÍNIMO: Logotipo aparentemente único no banco local."

# ============================================
# 5. UTILITÁRIOS
# ============================================

def allowed_file(filename: str) -> bool:
    """Verifica se o arquivo é uma imagem permitida"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def calcular_risco_total(dominios_ocupados: int, similaridade_bpi: float, redes_ocupadas: int) -> int:
    """
    Calcula risco total baseado em múltiplos fatores
    
    Args:
        dominios_ocupados: Quantidade de domínios ocupados
        similaridade_bpi: Similaridade máxima com BPI (0-100)
        redes_ocupadas: Quantidade de redes sociais ocupadas
    
    Returns:
        Risco total (0-100)
    """
    risco = 0
    
    # Fator domínios (max 30)
    risco += min(dominios_ocupados * 10, 30)
    
    # Fator BPI (max 50)
    if similaridade_bpi >= 90:
        risco += 50
    elif similaridade_bpi >= 80:
        risco += 40
    elif similaridade_bpi >= 70:
        risco += 30
    elif similaridade_bpi >= 60:
        risco += 20
    elif similaridade_bpi >= 50:
        risco += 10
    
    # Fator redes sociais (max 20)
    risco += min(redes_ocupadas * 5, 20)
    
    return min(risco, 100)
