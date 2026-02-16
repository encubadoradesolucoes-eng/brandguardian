import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Buscar chocolata
    cursor.execute("SELECT brand_name, process_number FROM ipi_record WHERE brand_name ILIKE '%chocolata%'")
    results = cursor.fetchall()
    
    print(f"Resultados para 'chocolata': {len(results)}")
    for r in results:
        print(f"  - {r[0]} (Processo: {r[1]})")
    
    # Listar TODAS as marcas
    cursor.execute("SELECT brand_name FROM ipi_record ORDER BY brand_name LIMIT 20")
    all_brands = cursor.fetchall()
    print(f"\nPrimeiras 20 marcas na base:")
    for b in all_brands:
        print(f"  - {b[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"ERRO: {e}")
