import fitz

def analyze_toc():
    # Tenta abrir o PDF que sabemos que existe no diretorio
    import os
    files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if not files:
        print("Nenhum PDF encontrado.")
        return
    
    pdf_path = files[0] # Pega o primeiro PDF (provavelmente o BPI)
    print(f"Analisando Índice de: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    
    # Geralmente o indice esta nas primeiras 5 paginas
    for i in range(min(5, len(doc))):
        page = doc[i]
        text = page.get_text()
        print(f"\n--- PAGINA {i+1} ---\n")
        # Imprimir apenas as primeiras linhas ou linhas que parecem indice
        lines = text.split('\n')
        for line in lines:
            if "...." in line or len(line.strip()) < 5: # Indices costumam ter pontinhos
                print(line)
            if "SUMÁRIO" in line.upper() or "INDICE" in line.upper():
                 print(f"ACHEI O TITULO DO INDICE: {line}")

if __name__ == "__main__":
    analyze_toc()
