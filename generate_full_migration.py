import os
import sqlite3
from sqlalchemy import create_engine
from app import app, db

# Caminhos
sqlite_path = os.path.join('database', 'brands.db')
output_sql = 'full_supabase_setup.sql'

def generate_full_dump():
    # 1. Gerar DDL (CREATE TABLE) para PostgreSQL
    # Criamos um engine de "mock" postgres para o SQLAlchemy gerar a sintaxe correta
    engine = create_engine('postgresql://')
    
    with open(output_sql, 'w', encoding='utf-8') as f:
        f.write("-- ==========================================\n")
        f.write("-- M24 BRAND GUARDIAN - SUPABASE SETUP\n")
        f.write("-- ==========================================\n\n")
        f.write("BEGIN;\n")
        f.write("SET session_replication_role = 'replica';\n\n")

        # Gerar os CREATE TABLE
        print("🏗️ Gerando DDL (Estrutura)...")
        for table in db.metadata.sorted_tables:
            # Traduz a tabela do app para SQL Postgres
            create_stmt = str(db.get_engine(app).raw_connection().connection.execute(f"SELECT sql FROM sqlite_master WHERE name='{table.name}'").fetchone()[0])
            # Infelizmente, o SQLite dump não serve para Postgres. 
            # Vamos usar uma abordagem mais robusta:
            pass
        
        # Correção: O método mais rápido para DDL Postgres via SQLAlchemy
        def dump(sql, *multiparams, **params):
            f.write(str(sql.compile(dialect=engine.dialect)).replace('DATETIME', 'TIMESTAMP') + ";\n")
        
        mock_engine = create_engine('postgresql://', strategy='mock', executor=dump)
        db.metadata.create_all(mock_engine)
        
        f.write("\n-- ==========================================\n")
        f.write("-- DATA INSERTION\n")
        f.write("-- ==========================================\n\n")

        # 2. Gerar Inserts (Dados)
        src = sqlite3.connect(sqlite_path)
        cursor = src.cursor()
        
        for table in db.metadata.sorted_tables:
            table_name = table.name
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            cols = [f'"{c[1]}"' for c in cursor.fetchall()]
            
            cursor.execute(f"SELECT * FROM \"{table_name}\"")
            rows = cursor.fetchall()
            
            if not rows: continue
            
            print(f"📦 Extraindo dados: {table_name}")
            for row in rows:
                values = []
                for val in row:
                    if val is None: values.append("NULL")
                    elif isinstance(val, bool): values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, (int, float)): values.append(str(val))
                    else:
                        escaped = str(val).replace("'", "''")
                        values.append(f"'{escaped}'")
                
                f.write(f"INSERT INTO \"{table_name}\" ({', '.join(cols)}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;\n")
        
        f.write("\nSET session_replication_role = 'origin';\n")
        f.write("COMMIT;")

    print(f"\n✅ ARQUIVO GERADO: {output_sql}")
    print("🚀 Ação: Copia TUDO deste arquivo e cola no SQL Editor do Supabase.")

if __name__ == "__main__":
    generate_full_dump()
