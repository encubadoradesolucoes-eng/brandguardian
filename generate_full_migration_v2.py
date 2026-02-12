import os
import sqlite3
from sqlalchemy import create_engine
from app import app, db

sqlite_path = os.path.join('database', 'brands.db')
output_sql = 'full_supabase_setup.sql'

def generate_full_dump():
    # Engine Mock para Postgres
    pg_engine = create_engine('postgresql://')
    
    with app.app_context():
        with open(output_sql, 'w', encoding='utf-8') as f:
            f.write("BEGIN;\n")
            f.write("SET session_replication_role = 'replica';\n\n")

            # 1. Gerar DDL via SQLAlchemy Mock
            def dump(sql, *multiparams, **params):
                compiled = sql.compile(dialect=pg_engine.dialect)
                sql_str = str(compiled).replace('DATETIME', 'TIMESTAMP').replace('BOOLEAN', 'BOOLEAN')
                f.write(sql_str + ";\n")
            
            mock_engine = create_engine('postgresql://', strategy='mock', executor=dump)
            db.metadata.create_all(mock_engine)
            
            f.write("\n")

            # 2. Dados do SQLite
            src = sqlite3.connect(sqlite_path)
            cursor = src.cursor()
            
            for table_name in db.metadata.tables.keys():
                cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                cols = [f'"{c[1]}"' for c in cursor.fetchall()]
                
                cursor.execute(f"SELECT * FROM \"{table_name}\"")
                rows = cursor.fetchall()
                if not rows: continue
                
                print(f"📦 Exportando: {table_name}")
                for row in rows:
                    values = []
                    for val in row:
                        if val is None: values.append("NULL")
                        elif isinstance(val, bool): values.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (int, float)): values.append(str(val))
                        else:
                            values.append(f"'{str(val).replace(\"'\", \"''\")}'")
                    
                    f.write(f"INSERT INTO \"{table_name}\" ({', '.join(cols)}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;\n")
            
            f.write("\nSET session_replication_role = 'origin';\n")
            f.write("COMMIT;")
            
    print(f"✅ Arquivo {output_sql} pronto.")

if __name__ == "__main__":
    generate_full_dump()
