
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    marker = "# ========== MÓDULO PURIFICAÇÃO (GLOBAL CHECK) =========="
    
    first_idx = content.find(marker)
    second_idx = content.find(marker, first_idx + 1)
    
    if first_idx != -1 and second_idx != -1:
        print(f"Duplicata encontrada! Primeira em {first_idx}, Segunda em {second_idx}.")
        
        # Apagar do primeiro até o segundo
        # O segundo deve ser mantido, pois é o inicio do bloco bom.
        
        new_content = content[:first_idx] + content[second_idx:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Bloco duplicado removido com sucesso!")
    else:
        print("Não foram encontradas duas cópias do marcador. Talvez já esteja limpo?")
        # Se não achou marcador, procura por start_purification duplicado manualmente?
        # Mas visualmente vimos 2 blocos iguais. O script vai achar.

except Exception as e:
    print(f"Erro: {e}")
