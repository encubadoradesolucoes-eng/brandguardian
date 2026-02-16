import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL')
if '?' not in url: url += '?sslmode=require'

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM ipi_record WHERE image_path IS NOT NULL")
    count_ipi = cur.fetchone()[0]
    print(f"IPI records with image: {count_ipi}")
    
    cur.execute("SELECT count(*) FROM brand WHERE logo_path IS NOT NULL")
    count_brand = cur.fetchone()[0]
    print(f"Brand records with logo: {count_brand}")
    
    if count_ipi > 0:
        cur.execute("SELECT image_path FROM ipi_record WHERE image_path IS NOT NULL LIMIT 5")
        print("IPI Samples:", cur.fetchall())
        
    if count_brand > 0:
        cur.execute("SELECT logo_path FROM brand WHERE logo_path IS NOT NULL LIMIT 5")
        print("Brand Samples:", cur.fetchall())
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
