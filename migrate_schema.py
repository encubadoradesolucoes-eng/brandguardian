"""
Script de Migração - Adiciona novas colunas ao banco de dados
Atualiza schema sem perder dados existentes
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Adiciona novas colunas às tabelas existentes"""
    
    db_path = os.path.join('database', 'brands.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado. Execute migrate_db.py primeiro.")
        return
    
    print("🔄 Iniciando migração do banco de dados...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Adicionar colunas de assinatura ao User (se não existirem)
        print("\n[1/5] Migrando tabela User...")
        
        # Verificar se colunas já existem
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'subscription_plan' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN subscription_plan VARCHAR(50) DEFAULT 'free'")
            print("   ✅ Coluna 'subscription_plan' adicionada")
        
        if 'subscription_start' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN subscription_start DATETIME")
            print("   ✅ Coluna 'subscription_start' adicionada")
        
        if 'subscription_end' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN subscription_end DATETIME")
            print("   ✅ Coluna 'subscription_end' adicionada")
        
        if 'max_brands' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN max_brands INTEGER DEFAULT 5")
            print("   ✅ Coluna 'max_brands' adicionada")
        
        # 2. Criar tabela SubscriptionPlan (se não existir)
        print("\n[2/5] Criando tabela SubscriptionPlan...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                price_monthly FLOAT NOT NULL,
                max_brands INTEGER NOT NULL,
                features TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        print("   ✅ Tabela 'subscription_plan' criada")
        
        # 3. Criar tabela RPIMonitoring (se não existir)
        print("\n[3/5] Criando tabela RPIMonitoring...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpi_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rpi_number VARCHAR(50) UNIQUE NOT NULL,
                publication_date DATETIME,
                processed BOOLEAN DEFAULT 0,
                total_new_marks INTEGER DEFAULT 0,
                conflicts_detected INTEGER DEFAULT 0,
                data_file VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Tabela 'rpi_monitoring' criada")
        
        # 4. Criar tabela BrandConflict (se não existir)
        print("\n[4/5] Criando tabela BrandConflict...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_conflict (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                rpi_id INTEGER,
                conflicting_mark_name VARCHAR(200),
                conflicting_mark_number VARCHAR(50),
                similarity_score FLOAT,
                conflict_type VARCHAR(50),
                status VARCHAR(50) DEFAULT 'pending',
                notified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brand(id),
                FOREIGN KEY (rpi_id) REFERENCES rpi_monitoring(id)
            )
        """)
        print("   ✅ Tabela 'brand_conflict' criada")
        
        # 5. Criar tabela Payment (se não existir)
        print("\n[5/5] Criando tabela Payment...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name VARCHAR(50),
                amount FLOAT NOT NULL,
                currency VARCHAR(3) DEFAULT 'MZN',
                payment_method VARCHAR(50),
                phone_number VARCHAR(20),
                mpesa_transaction_id VARCHAR(100),
                mpesa_conversation_id VARCHAR(100),
                reference VARCHAR(100) UNIQUE,
                status VARCHAR(50) DEFAULT 'pending',
                response_code VARCHAR(50),
                response_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        print("   ✅ Tabela 'payment' criada")
        
        conn.commit()
        print("\n✅ Migração concluída com sucesso!")
        print("\n📊 Próximo passo: Execute 'python seed_plans.py' para popular os planos")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro durante migração: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
