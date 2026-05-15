import psycopg2

db_url = "postgresql://postgres.austbyfpjimfjrtuvujx:pandorabox5229@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

print("Tentando conectar à base de dados para adicionar a coluna...")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Adicionar a coluna
    cur.execute('ALTER TABLE "user" ADD COLUMN popup_dismissed_at TIMESTAMP;')
    conn.commit()
    
    print("Sucesso! Coluna popup_dismissed_at adicionada à tabela 'user'.")
    cur.close()
    conn.close()
except Exception as e:
    if "already exists" in str(e):
        print("A coluna popup_dismissed_at já existe na tabela 'user'.")
    else:
        print(f"\nErro: {e}")
