import fitz
import os

def debug_text():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bpi_file = None
    for f in os.listdir(current_dir):
        if "BPI 170" in f and f.endswith(".pdf"):
            bpi_file = os.path.join(current_dir, f)
            break
            
    if not bpi_file: return

    doc = fitz.open(bpi_file)
    
    # Procurar página com "LOGÓTIPOS"
    found_page = None
    for i, page in enumerate(doc):
        text = page.get_text()
        if "LOGÓTIPOS" in text and "Pedidos" in text:
            print(f"✅ Seção Logótipos encontrada na página {i+1}")
            found_page = page
            # Imprimir um pedaço do texto para ver o formato do L.Nº
            print("\n--- AMOSTRA DE TEXTO ---")
            print(text[:1000])
            break
            
if __name__ == '__main__':
    debug_text()
