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
    cur.execute("SELECT count(*) FROM ipi_record WHERE image_path IS NOT NULL")
    print(f"IPI with image: {cur.fetchone()[0]}")
    cur.execute("SELECT brand_name, image_path FROM ipi_record WHERE image_path IS NOT NULL LIMIT 5")
    print("Samples:", cur.fetchall())
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
