import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL')
if '?' not in url: url += '?sslmode=require'

# Configuração do Pooler (ajuste se necessário)
url = url.replace("postgres:", "postgres.austbyfpjimfjrtuvujx:")

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Lista arquivos na pasta de imagens do IPI
    img_dir = 'static/ipi_images'
    if not os.path.exists(img_dir):
        print(f"ERRO: Diretorio {img_dir} nao encontrado!")
        exit()
        
    files = [f for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    print(f"Encontrados {len(files)} arquivos de imagem.")
    
    updated = 0
    for filename in files:
        # Tenta extrair o numero do processo do nome do arquivo
        # Exemplo: logo_2526_2023.png -> 2526/2023
        parts = filename.replace('logo_', '').replace('.png', '').replace('.jpg', '').replace('.jpeg', '').split('_')
        if len(parts) >= 2:
            proc_no = f"{parts[0]}/{parts[1]}"
            
            # Atualiza o registro no banco
            cur.execute("UPDATE ipi_record SET image_path = %s WHERE process_number ILIKE %s", (filename, f"%{proc_no}%"))
            if cur.rowcount > 0:
                print(f"✅ Vinculado: {filename} -> {proc_no}")
                updated += 1
            else:
                # Tenta busca exata se a parcial falhar
                cur.execute("UPDATE ipi_record SET image_path = %s WHERE process_number = %s", (filename, proc_no))
                if cur.rowcount > 0:
                    print(f"✅ Vinculado (exato): {filename} -> {proc_no}")
                    updated += 1
                else:
                    # Tenta vincular pela marca se o nome for idêntico (fallback radical)
                    # No seu manual/dump, os ids de imagem parecem seguir padrões de processo
                    pass

    conn.commit()
    print(f"\nSincronização concluída! {updated} registros atualizados com sucesso.")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Erro fatal: {e}")
