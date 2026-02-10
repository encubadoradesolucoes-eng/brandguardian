import sqlite3
import os

def update_db():
    db_path = r"c:\Users\Acer\Documents\tecnologias\brandguardian\database\brands.db"
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado em {db_path}")
        return

    print("🛠️ Verificando e Corrigindo esquema da tabela 'user'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("last_active", "DATETIME"),
        ("agent_registration_number", "VARCHAR(50)"),
        ("agent_bio", "TEXT"),
        ("subscription_plan", "VARCHAR(50)"),
        ("subscription_start", "DATETIME"),
        ("subscription_end", "DATETIME"),
        ("max_brands", "INTEGER")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            print(f"✅ Coluna '{col_name}' adicionada.")
        except sqlite3.OperationalError:
            print(f"ℹ️ Coluna '{col_name}' já existe.")
            
    conn.commit()
    conn.close()
    print("🚀 Verificação concluída!")

if __name__ == '__main__':
    update_db()
