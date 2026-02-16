import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Conectar ao Supabase
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"DATABASE_URL: {DATABASE_URL[:50]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Testar query simples
    cursor.execute("SELECT COUNT(*) FROM ipi_record")
    count = cursor.fetchone()[0]
    print(f"\n✅ Total de registos IpiRecord: {count}")
    
    # Buscar "Cartrack"
    cursor.execute("SELECT * FROM ipi_record WHERE brand_name ILIKE '%cartrack%'")
    results = cursor.fetchall()
    print(f"\n🔍 Resultados para 'Cartrack': {len(results)} encontrados")
    for r in results:
        print(f"  - {r[5]} (Processo: {r[1]})")
    
    cursor.close()
    conn.close()
    print("\n✅ Conexão OK!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
