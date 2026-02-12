import sqlite3
import os

sqlite_path = os.path.join('database', 'brands.db')
dump_path = 'supabase_final_dump.sql'

def generate_pro_dump():
    if not os.path.exists(sqlite_path):
        print(f"❌ Erro: {sqlite_path} não encontrado.")
        return

    src = sqlite3.connect(sqlite_path)
    cursor = src.cursor()
    
    # Obter apenas as tabelas criadas pelo usuário
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [t[0] for t in cursor.fetchall()]
    
    with open(dump_path, 'w', encoding='utf-8') as f:
        # Desabilita triggers e chaves estrangeiras para evitar erros de ordem de inserção
        f.write("BEGIN;\n")
        f.write("SET session_replication_role = 'replica';\n\n")
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info(\"{table}\")")
            columns = [f'"{c[1]}"' for c in cursor.fetchall()]
            
            cursor.execute(f"SELECT * FROM \"{table}\"")
            rows = cursor.fetchall()
            
            if not rows:
                continue
                
            print(f"📦 Exportando {len(rows)} registros de: {table}")
            f.write(f"-- Dados da tabela {table}\n")
            
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, bool):
                        values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        # Escapar aspas simples para Postgres
                        escaped = str(val).replace("'", "''")
                        values.append(f"'{escaped}'")
                
                f.write(f"INSERT INTO \"{table}\" ({', '.join(columns)}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;\n")
            f.write("\n")
            
        f.write("SET session_replication_role = 'origin';\n")
        f.write("COMMIT;")
    
    src.close()
    print(f"✅ Sucesso! O arquivo {dump_path} está pronto para ser colado no SQL Editor do Supabase.")

if __name__ == "__main__":
    generate_pro_dump()
