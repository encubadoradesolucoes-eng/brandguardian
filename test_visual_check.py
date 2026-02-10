"""
Teste simples da verificação visual
"""
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from modules.real_scanner import verificacao_imagem_real
from modules.image_matcher import DuplicateImageFinder

def test_basic_visual_check():
    """Testa a verificação visual básica"""
    print("=" * 60)
    print("TESTE DA VERIFICAÇÃO VISUAL")
    print("=" * 60)
    
    with app.app_context():
        # Verifica se há imagens no sistema
        from app import IpiRecord, Brand
        
        ipi_count = IpiRecord.query.filter(IpiRecord.image_path.isnot(None)).count()
        brand_count = Brand.query.filter(Brand.logo_path.isnot(None)).count()
        
        print(f"\n📊 Estatísticas do Banco:")
        print(f"   - Registros BPI com imagem: {ipi_count}")
        print(f"   - Marcas de usuários com logo: {brand_count}")
        print(f"   - Total para comparação: {ipi_count + brand_count}")
        
        # Testa a classe DuplicateImageFinder
        print("\n🔧 Teste do DuplicateImageFinder:")
        app_root = os.path.dirname(__file__)
        finder = DuplicateImageFinder(app_root)
        print(f"   - Instância criada: ✓")
        print(f"   - Base path: {finder.base_path}")
        
        # Verifica diretórios
        print("\n📁 Verificando Diretórios:")
        dirs_to_check = [
            'static/uploads',
            'uploads',
            'static/ipi_images',
            'ipi_images'
        ]
        
        for dir_name in dirs_to_check:
            full_path = os.path.join(app_root, dir_name)
            exists = os.path.exists(full_path)
            if exists:
                files = len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])
                print(f"   - {dir_name}: ✓ ({files} arquivos)")
            else:
                print(f"   - {dir_name}: ✗ (não existe)")
        
        # Testa com uma imagem se existir
        test_image = None
        
        # Procura uma imagem de teste
        if brand_count > 0:
            sample_brand = Brand.query.filter(Brand.logo_path.isnot(None)).first()
            if sample_brand:
                for search_dir in ['static/uploads', 'uploads']:
                    test_path = os.path.join(app_root, search_dir, sample_brand.logo_path)
                    if os.path.exists(test_path):
                        test_image = test_path
                        break
        
        if test_image:
            print(f"\n🖼️  Testando com imagem real: {os.path.basename(test_image)}")
            try:
                resultados = verificacao_imagem_real(test_image, "Teste")
                
                print(f"   - Status: ✓ Análise concluída")
                print(f"   - Métodos utilizados: {len(resultados.get('metodos_utilizados', []))}")
                print(f"   - Análises realizadas: {len(resultados.get('analises', []))}")
                print(f"   - Conflitos encontrados: {len(resultados.get('conflitos_visuais', []))}")
                
                if resultados.get('resumo'):
                    print(f"\n📋 Resumo:")
                    resumo = resultados['resumo']
                    print(f"   - Nível de Risco: {resumo.get('nivel_risco_visual')}")
                    print(f"   - Risco Visual: {resumo.get('risco_visual')}%")
                    print(f"   - Recomendação: {resumo.get('recomendacao')[:100]}...")
                
                if resultados.get('conflitos_visuais'):
                    print(f"\n⚠️  Primeiros 3 Conflitos:")
                    for conf in resultados['conflitos_visuais'][:3]:
                        print(f"   - {conf['marca_bpi']}: {conf['similaridade_media']}% ({conf['gravidade']})")
                
            except Exception as e:
                print(f"   - Erro na análise: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠️  Nenhuma imagem de teste disponível no sistema")
            print("   Adicione algumas marcas com logos para testar")
        
        print("\n" + "=" * 60)
        print("TESTE CONCLUÍDO")
        print("=" * 60)

if __name__ == '__main__':
    test_basic_visual_check()
