from app import app, db, IpiRecord
from modules.bpi_importer import BPIImporter
import os

def reset_and_import():
    print("🧹 [1/2] Limpando registros de Tabela com status incorreto...")
    with app.app_context():
        # Apagar registros que vieram de tabelas (sem imagem recortada) para corrigir status
        # Cuidado para não apagar logotipos visuais trabalhoso
        # Mas Caducidade pode ter sido salva como Concessao.
        
        # Estratégia: Apagar TUDO que não seja Logotipo Visual (image_path != None)
        # OU ser drástico e apagar tudo para garantir integridade.
        # Dado que extração visual é rápida (19 imagens), melhor apagar tudo.
        
        deleted = IpiRecord.query.delete()
        db.session.commit()
        print(f"✅ {deleted} registros apagados. Banco limpo.")

    print("\n🚀 [2/2] Re-importando BPI 170 com correção de status...")
    
    # Achar o arquivo
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bpi_file = None
    for f in os.listdir(current_dir):
        if "BPI 170" in f and f.endswith(".pdf"):
            bpi_file = os.path.join(current_dir, f)
            break
            
    if bpi_file:
         with app.app_context():
            importer = BPIImporter(bpi_file)
            importer.run()
    else:
        print("❌ Arquivo PDF não encontrado.")

if __name__ == '__main__':
    reset_and_import()
