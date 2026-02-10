try:
    from modules.bpi_importer import BPIImporter
    print("✅ Módulo BPIImporter carregado com sucesso!")
except ImportError as e:
    print(f"❌ Erro de Importação: {e}")
except SyntaxError as e:
    print(f"❌ Erro de Sintaxe: {e}")
except Exception as e:
    print(f"❌ Erro Genérico: {e}")
