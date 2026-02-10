import re

try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Procura definições duplicadas da rota de purificação
    pattern = r"@app\.route\(['\"]/admin/purification['\"]\)"
    matches = list(re.finditer(pattern, content))

    if len(matches) > 1:
        print(f"⚠️ Encontradas {len(matches)} definições de '/admin/purification'. Desativando a primeira...")
        
        # Estratégia: Comentar a primeira anotação @app.route
        first_match_index = matches[0].start()
        
        # Reconstrói o conteúdo alterando apenas a primeira ocorrência
        new_content = (
            content[:first_match_index] + 
            "# DUPLICATE_REMOVED " + 
            content[first_match_index:]
        )
        
        # Também procurar e comentar a função purification_page() associada logo abaixo
        # Mas só comentar a rota já resolve o erro de 'View function mapping is overwriting'.
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Rota duplicada desativa. O servidor deve iniciar agora.")
    else:
        print("✅ Nenhuma duplicação encontrada para '/admin/purification'.")
        
    # Verificar também /api/purification/start
    pattern2 = r"@app\.route\(['\"]/api/purification/start['\"]"
    matches2 = list(re.finditer(pattern2, content))
    if len(matches2) > 1:
         print(f"Fixing duplicate /api/purification/start...")
         idx = matches2[0].start()
         with open('app.py', 'r', encoding='utf-8') as f: content = f.read() # reload
         new_content = content[:idx] + "# DUP " + content[idx:]
         with open('app.py', 'w', encoding='utf-8') as f: f.write(new_content)

except Exception as e:
    print(f"Erro: {e}")
