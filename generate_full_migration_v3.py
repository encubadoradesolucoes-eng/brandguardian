import os
import sqlite3
from app import app, db

sqlite_path = os.path.join('database', 'brands.db')
output_sql = 'full_supabase_setup.sql'

def get_pg_type(col):
    t = str(col.type).upper()
    # Para evitar erros de "value too long" em migrações rápidas, 
    # convertemos VARCHAR limitado para TEXT no Postgres.
    if 'VARCHAR' in t: return 'TEXT'
    if 'INTEGER' in t: return 'SERIAL' if col.primary_key else 'INTEGER'
    if 'TEXT' in t: return 'TEXT'
    if 'DATETIME' in t: return 'TIMESTAMP'
    if 'TIMESTAMP' in t: return 'TIMESTAMP'
    if 'BOOLEAN' in t: return 'BOOLEAN'
    if 'FLOAT' in t: return 'DOUBLE PRECISION'
    return 'TEXT'

def generate_full_dump():
    with app.app_context():
        with open(output_sql, 'w', encoding='utf-8') as f:
            f.write("BEGIN;\n")
            f.write("SET session_replication_role = 'replica';\n\n")

            # 1. DDL
            for table_name, table in db.metadata.tables.items():
                # Drop table if exists para permitir re-execução limpa se necessário
                f.write(f"DROP TABLE IF EXISTS \"{table_name}\" CASCADE;\n")
                f.write(f"CREATE TABLE \"{table_name}\" (\n")
                col_defs = []
                for col in table.columns:
                    line = f"  \"{col.name}\" {get_pg_type(col)}"
                    if col.primary_key: line += " PRIMARY KEY"
                    if not col.nullable: line += " NOT NULL"
                    if col.unique: line += " UNIQUE"
                    col_defs.append(line)
                f.write(",\n".join(col_defs))
                f.write("\n);\n\n")

            # 2. DATA
            src = sqlite3.connect(sqlite_path)
            cursor = src.cursor()
            for table_name, table in db.metadata.tables.items():
                cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                cols = [f'"{c[1]}"' for c in cursor.fetchall()]
                
                col_types = {col.name: str(col.type).upper() for col in table.columns}
                
                cursor.execute(f"SELECT * FROM \"{table_name}\"")
                rows = cursor.fetchall()
                if not rows: continue
                
                print(f"📦 Extraindo: {table_name}")
                for row in rows:
                    vals = []
                    for i, v in enumerate(row):
                        col_name = table.columns[i].name
                        is_bool_col = 'BOOLEAN' in col_types.get(col_name, '')
                        
                        if v is None: 
                            vals.append("NULL")
                        elif is_bool_col:
                            vals.append("TRUE" if v in (1, True, '1', 'True') else "FALSE")
                        elif isinstance(v, bool): 
                            vals.append("TRUE" if v else "FALSE")
                        elif isinstance(v, (int, float)): 
                            vals.append(str(v))
                        else: 
                            vals.append("'" + str(v).replace("'", "''") + "'")
                    
                    f.write(f"INSERT INTO \"{table_name}\" ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT DO NOTHING;\n")
            
            f.write("\nSET session_replication_role = 'origin';\n")
            f.write("COMMIT;")
            
    print(f"✅ Arquivo {output_sql} atualizado com TEXT para evitar truncamento.")

if __name__ == "__main__":
    generate_full_dump()
