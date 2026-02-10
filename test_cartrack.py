"""
Teste direto do scan_live_real com CARTRACK
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configura Flask app context antes de importar
from app import app

def test_cartrack():
    print("=" * 60)
    print("TESTE: scan_live_real com 'CARTRAK' (erro de digitação)")
    print("Deve encontrar 'CARTRACK' via busca fonética")
    print("=" * 60)
    
    with app.app_context():
        from modules.real_scanner import scan_live_real
        
        # Testa com usuário logado (mais detalhes)
        print("\n[1] Testando com usuario_logado=True...")
        resultado = scan_live_real("CARTRAK", usuario_logado=True)
        
        print(f"\n✓ Termo: {resultado.get('termo')}")
        print(f"✓ Timestamp: {resultado.get('timestamp')}")
        
        # Domínios
        print(f"\n--- DOMÍNIOS ({len(resultado.get('dominios', []))}) ---")
        for dom in resultado.get('dominios', [])[:5]:
            print(f"  {dom['dominio']}: {dom['status']}")
        
        # BPI
        bpi_results = resultado.get('bpi', [])
        print(f"\n--- BPI ({len(bpi_results)} resultados) ---")
        if bpi_results:
            for i, marca in enumerate(bpi_results[:5], 1):
                print(f"  {i}. {marca['marca']} - {marca['similaridade']}% similar")
                print(f"     Processo: {marca['processo']}")
                print(f"     Status: {marca['status']}")
        else:
            print("  ⚠️ NENHUMA marca encontrada no BPI!")
        
        # Redes Sociais
        print(f"\n--- REDES SOCIAIS ({len(resultado.get('redes_sociais', []))}) ---")
        for rede in resultado.get('redes_sociais', []):
            print(f"  {rede['plataforma']}: {rede['status']} (confiança: {rede['confianca']}%)")
        
        # Análise de Risco
        risco = resultado.get('analise_risco', {})
        print(f"\n--- ANÁLISE DE RISCO ---")
        print(f"  Risco Total: {risco.get('risco_total')}/100")
        print(f"  Nível: {risco.get('nivel_risco')}")
        print(f"  Recomendação: {risco.get('recomendacao')}")
        
        # Fatores de risco
        if risco.get('fatores'):
            print(f"\n  Fatores detectados:")
            for fator in risco['fatores']:
                print(f"    - {fator.get('fator')} (peso: {fator.get('peso')})")
        
        # Limites/Erros
        if resultado.get('limites'):
            print(f"\n--- LIMITES/AVISOS ---")
            for limite in resultado['limites']:
                print(f"  ⚠️ {limite}")
        
        print("\n" + "=" * 60)
        print("TESTE CONCLUÍDO")
        print("=" * 60)
        
        return resultado

if __name__ == "__main__":
    try:
        test_cartrack()
    except Exception as e:
        import traceback
        print("\n" + "!" * 60)
        print("ERRO NO TESTE:")
        print("!" * 60)
        print(traceback.format_exc())
        sys.exit(1)
