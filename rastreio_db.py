import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL')
# Garantir o username do pooler
if 'postgres:' in url:
    url = url.replace("postgres:", "postgres.austbyfpjimfjrtuvujx:")
if '?' not in url: url += '?sslmode=require'

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # 1. Rastrear Colunas REAIS da tabela
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ipi_record'")
    columns = cur.fetchall()
    print("--- COLUNAS EM ipi_record ---")
    for col in columns:
        print(f"Col: {col['column_name']} | Tipo: {col['data_type']}")
    
    # 2. Rastrear Dados REAIS (ver se image_path tem algo)
    cur.execute("SELECT brand_name, image_path, process_number FROM ipi_record WHERE brand_name IS NOT NULL LIMIT 10")
    rows = cur.fetchall()
    print("\n--- AMOSTRA DE DADOS ---")
    for row in rows:
        print(f"Marca: {row['brand_name']} | Img: {row['image_path']} | Proc: {row['process_number']}")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"ERRO DE RASTREIO: {e}")
