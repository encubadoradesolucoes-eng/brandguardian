import sqlite3
import os

sqlite_path = os.path.join('database', 'brands.db')
dump_path = 'data_supabase.sql'

def generate_pg_dump():
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    with open(dump_path, 'w', encoding='utf-8') as f:
        f.write("-- Supabase Data Dump\n")
        f.write("SET session_replication_role = 'replica'; -- Disable triggers/FKs\n\n")
        
        for table in tables:
            print(f"Exporting {table}...")
            cursor.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            if not rows:
                continue
                
            f.write(f"-- Data for {table}\n")
            for row in rows:
                # Format values for Postgres
                formatted_values = []
                for val in row:
                    if val is None:
                        formatted_values.append("NULL")
                    elif isinstance(val, bool):
                        formatted_values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, (int, float)):
                        formatted_values.append(str(val))
                    else:
                        # String escaping
                        escaped = str(val).replace("'", "''")
                        formatted_values.append(f"'{escaped}'")
                
                col_names = ", ".join(columns)
                val_str = ", ".join(formatted_values)
                f.write(f"INSERT INTO \"{table}\" ({col_names}) VALUES ({val_str});\n")
            f.write("\n")
            
        f.write("SET session_replication_role = 'origin'; -- Re-enable triggers\n")
    
    conn.close()
    print(f"✅ Gerado: {dump_path}")

if __name__ == "__main__":
    generate_pg_dump()
