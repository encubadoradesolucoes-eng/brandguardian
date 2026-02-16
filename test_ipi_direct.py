import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

# Corrigir URL se necessário
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Adicionar SSL
if DATABASE_URL and 'sslmode' not in DATABASE_URL:
    if '?' not in DATABASE_URL:
        DATABASE_URL += '?sslmode=require'
    else:
        DATABASE_URL += '&sslmode=require'

print(f"Conectando a: {DATABASE_URL[:50]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Teste 1: Verificar se a tabela existe
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ipi_record')")
    exists = cursor.fetchone()[0]
    print(f"\nTabela ipi_record existe? {exists}")
    
    if exists:
        # Teste 2: Contar registros
        cursor.execute("SELECT COUNT(*) FROM ipi_record")
        count = cursor.fetchone()[0]
        print(f"Total de registros: {count}")
        
        # Teste 3: Buscar Cartrack
        cursor.execute("SELECT brand_name, process_number FROM ipi_record WHERE brand_name ILIKE '%cartrack%'")
        results = cursor.fetchall()
        print(f"\nResultados para 'cartrack': {len(results)}")
        for r in results:
            print(f"  - {r[0]} (Processo: {r[1]})")
        
        # Teste 4: Buscar chocolata/shocolata
        cursor.execute("SELECT brand_name, process_number FROM ipi_record WHERE brand_name ILIKE '%chocolata%' OR brand_name ILIKE '%shocolata%'")
        results = cursor.fetchall()[0:10]
        print(f"\nResultados para 'chocolata/shocolata': {len(results)}")
        for r in results:
            print(f"  - {r[0]} (Processo: {r[1]})")
    
    cursor.close()
    conn.close()
    print("\n✅ CONEXÃO FUNCIONANDO!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
