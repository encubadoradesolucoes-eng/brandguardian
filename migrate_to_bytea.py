import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL')
if 'postgres:' in url: url = url.replace("postgres:", "postgres.austbyfpjimfjrtuvujx:")
if '?' not in url: url += '?sslmode=require'

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # 1. Migrar IPI RECORDS
    img_dir = 'static/ipi_images'
    if os.path.exists(img_dir):
        files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"Lendo {len(files)} imagens de IPI...")
        for filename in files:
            path = os.path.join(img_dir, filename)
            with open(path, 'rb') as f:
                binary_data = f.read()
                # Tenta vincular pelo image_path que ja estava la ou pelo nome do arquivo
                cur.execute("UPDATE ipi_record SET image_data = %s WHERE image_path = %s OR image_path IS NULL AND brand_name IS NOT NULL", (psycopg2.Binary(binary_data), filename))
        print("✅ IPI Records atualizados.")

    # 2. Migrar BRANDS (Clientes)
    upload_dir = 'uploads'
    if os.path.exists(upload_dir):
        files = [f for f in os.listdir(upload_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"Lendo {len(files)} logos de clientes...")
        for filename in files:
            path = os.path.join(upload_dir, filename)
            with open(path, 'rb') as f:
                binary_data = f.read()
                cur.execute("UPDATE brand SET image_data = %s WHERE logo_path = %s", (psycopg2.Binary(binary_data), filename))
        print("✅ Brands atualizadas.")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🚀 Migração de BINÁRIOS concluída!")
except Exception as e:
    print(f"Erro: {e}")
