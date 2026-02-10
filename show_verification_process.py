"""
Demonstração detalhada de como o sistema verifica marcas
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from modules.real_scanner import scan_live_real
import json

def mostrar_processo_verificacao(termo: str):
    print("=" * 80)
    print(f"PROCESSO DE VERIFICAÇÃO: '{termo}'")
    print("=" * 80)
    
    with app.app_context():
        # Executa verificação
        resultados = scan_live_real(termo, usuario_logado=True)
        
        print("\n📋 MÉTODOS UTILIZADOS:")
        for i, metodo in enumerate(resultados.get('metodos_utilizados', []), 1):
            print(f"   {i}. {metodo}")
        
        print("\n" + "─" * 80)
        print("ETAPA 1: VERIFICAÇÃO DE DOMÍNIOS")
        print("─" * 80)
        print("Como funciona:")
        print("  1. Remove caracteres especiais do termo")
        print("  2. Testa domínios: .co.mz, .com, .org, .net, .info")
        print("  3. Usa DNS lookup (socket.gethostbyname)")
        print("  4. Se resolver IP = OCUPADO | Se falhar = DISPONÍVEL")
        print("\nResultados:")
        for d in resultados.get('dominios', []):
            icon = "❌" if d['status'] == 'OCUPADO' else "✅"
            print(f"  {icon} {d['dominio']}: {d['status']} (Confiança: {d['confianca']}%)")
        
        print("\n" + "─" * 80)
        print("ETAPA 2: CONSULTA NO BPI LOCAL")
        print("─" * 80)
        print("Como funciona:")
        print("  1. Busca SQL com ILIKE (case-insensitive)")
        print("  2. Procura termo contido em marcas registradas")
        print("  3. Gera variações fonéticas (CH→SH, Z→S, etc)")
        print("  4. Usa SequenceMatcher para calcular similaridade")
        print("  5. Usa jellyfish double_metaphone para fonética")
        print("\nResultados:")
        if resultados.get('bpi'):
            print(f"  📊 {len(resultados['bpi'])} marcas similares encontradas:")
            for marca in resultados['bpi'][:5]:  # Top 5
                print(f"     - {marca['marca']}: {marca['similaridade']}% similar")
                print(f"       Processo: {marca['processo']} | Classe: {marca['classe']}")
        else:
            print("  ✅ Nenhuma marca similar encontrada")
        
        print("\n" + "─" * 80)
        print("ETAPA 3: VERIFICAÇÃO DE REDES SOCIAIS")
        print("─" * 80)
        print("Como funciona:")
        print("  1. Faz requisição HTTP para instagram.com/{termo}")
        print("  2. Analisa código de resposta (200, 404, etc)")
        print("  3. Verifica conteúdo da página (heurísticas)")
        print("  4. Instagram: busca 'Sorry, this page isn't available'")
        print("  5. Facebook: busca 'page not found' ou redirect login")
        print("  6. LinkedIn: busca '404' ou 'page not found'")
        print("\nResultados:")
        for rede in resultados.get('redes_sociais', []):
            icon = "❌" if rede['status'] == 'OCUPADO' else "✅"
            print(f"  {icon} {rede['plataforma']}: {rede['status']} (Confiança: {rede['confianca']}%)")
            if rede.get('url'):
                print(f"     URL: {rede['url']}")
        
        print("\n" + "─" * 80)
        print("ETAPA 4: CÁLCULO DE RISCO")
        print("─" * 80)
        print("Fórmula:")
        print("  Risco Base = 10")
        print("  + Domínio .co.mz ocupado = +60 (CRÍTICO)")
        print("  + Outros domínios = +20")
        print("  + BPI similaridade ≥90% = +80")
        print("  + BPI similaridade ≥75% = +50")
        print("  + BPI similaridade ≥60% = +30")
        print("  + Redes sociais ocupadas = +20")
        print("  MÁXIMO = 100")
        print("\nCálculo para este termo:")
        
        analise = resultados.get('analise_risco', {})
        if analise.get('fatores'):
            for fator in analise['fatores']:
                print(f"  📌 {fator['fator']}")
                print(f"     Peso: +{fator['peso']} pontos")
                if fator.get('quantidade'):
                    print(f"     Quantidade: {fator['quantidade']}")
        
        print(f"\n  🎯 RISCO TOTAL: {analise.get('risco_total', 0)}/100")
        print(f"  🏷️  NÍVEL: {analise.get('nivel_risco', 'N/A')}")
        
        print("\n" + "─" * 80)
        print("CONCLUSÃO")
        print("─" * 80)
        recomendacao = analise.get('recomendacao', 'N/A')
        print(f"  {recomendacao}")
        
        print("\n" + "=" * 80)
        
        # Mostra JSON completo para debug
        print("\n📄 DADOS COMPLETOS (JSON):")
        print(json.dumps({
            'dominios_count': len(resultados.get('dominios', [])),
            'bpi_count': len(resultados.get('bpi', [])),
            'redes_count': len(resultados.get('redes_sociais', [])),
            'risco': analise.get('risco_total'),
            'nivel': analise.get('nivel_risco')
        }, indent=2))

if __name__ == '__main__':
    import sys
    
    # Pega termo da linha de comando ou usa exemplo
    termo = sys.argv[1] if len(sys.argv) > 1 else "NIKE"
    
    mostrar_processo_verificacao(termo)
