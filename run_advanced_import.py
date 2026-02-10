import os
from app import app
from modules.bpi_importer import BPIImporter

def run():
    # Localizar arquivo BPI no diretório ATUAL
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Procurar arquivo
    bpi_file = None
    for f in os.listdir(current_dir):
        if "BPI 170" in f and f.endswith(".pdf"):
            bpi_file = os.path.join(current_dir, f)
            break
            
    if bpi_file:
        print(f"[INFO] Arquivo para Analise Visual: {bpi_file}")
        with app.app_context():
            importer = BPIImporter(bpi_file)
            importer.run()
    else:
        print("[ERRO] Arquivo BPI 170 nao encontrado.")

if __name__ == '__main__':
    run()
