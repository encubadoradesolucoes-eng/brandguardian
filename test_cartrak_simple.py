"""
Teste simplificado para CARTRAK vs CARTRACK
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_cartrak():
    with app.app_context():
        from modules.real_scanner import scan_live_real
        
        print("\n" + "="*70)
        print("TESTE: CARTRAK (erro) deve encontrar CARTRACK (correto)")
        print("="*70)
        
        resultado = scan_live_real("CARTRAK", usuario_logado=True)
        
        # BPI Results
        bpi = resultado.get('bpi', [])
        print(f"\n📊 BPI: {len(bpi)} marcas encontradas")
        
        if bpi:
            print("\n✅ SUCESSO - Marcas similares detectadas:")
            for i, marca in enumerate(bpi[:10], 1):
                sim = marca['similaridade']
                nome = marca['marca']
                proc = marca['processo']
                
                # Destaca se encontrou CARTRACK
                destaque = " ⭐ MATCH!" if "CARTRACK" in nome.upper() else ""
                print(f"  {i}. {nome} - {sim}% similar{destaque}")
                print(f"     Processo: {proc}")
        else:
            print("\n❌ FALHA - Nenhuma marca encontrada!")
            print("   A busca fonética NÃO está funcionando corretamente.")
        
        # Análise de Risco
        risco = resultado.get('analise_risco', {})
        print(f"\n🎯 RISCO: {risco.get('risco_total')}/100 - {risco.get('nivel_risco')}")
        
        # Salva resultado completo
        with open('test_cartrak_result.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultado completo salvo em: test_cartrak_result.json")
        print("="*70 + "\n")
        
        return len(bpi) > 0

if __name__ == "__main__":
    try:
        sucesso = test_cartrak()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        import traceback
        print("\n❌ ERRO:")
        print(traceback.format_exc())
        sys.exit(1)
