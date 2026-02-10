
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Marcador de início seguro (última função boa conhecida)
    marker_start_text = "def analyze_csv_structure():"
    idx_start = content.find(marker_start_text)
    
    # Marcador do bloco NOVO e BOM (inserido pelo fix)
    marker_end_text = "# ========== MÓDULO PURIFICAÇÃO (GLOBAL CHECK) =========="
    idx_end = content.find(marker_end_text)
    
    if idx_start != -1 and idx_end != -1 and idx_end > idx_start:
        print(f"Limpando lixo entre {idx_start} e {idx_end}...")
        
        # Preservar a função analyze_csv e seu corpo.
        # Vamos assumir que ela tem um tamanho razoável ou procurar o próximo @app.route?
        # A analyze_csv_structure tinha ~50 linhas.
        # Vamos tentar achar onde ela termina? Difícil sem parser.
        
        # Alternativa: Comentar tudo nesse intervalo que pareça rota ou função
        # Mas isso pode quebrar a identação.
        
        # Vamos ser mais cirúrgicos: As duplicatas são APENAS purification_page, start_purification, status_purification.
        # Vamos comentar suas definições ANTIGAS (antes do idx_end)
        
        chunk = content[:idx_end] # Tudo antes do bloco novo
        
        # Comentar rotas antigas
        chunk = chunk.replace("@app.route('/admin/purification')", "# OLD_ROUTE /admin/purification")
        chunk = chunk.replace("@app.route('/api/purification/start')", "# OLD_ROUTE /api/purification/start")
        chunk = chunk.replace("@app.route('/api/purification/status')", "# OLD_ROUTE /api/purification/status")
        
        # Juntar com o resto
        final_content = chunk + content[idx_end:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        print("✅ Lixo antigo comentado com sucesso!")
        
    else:
        print("Makers not found or order invalid.")

except Exception as e:
    print(f"Erro: {e}")
