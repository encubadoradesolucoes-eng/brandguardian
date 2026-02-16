#!/bin/bash

# 1. Tabelas já existem no Supabase (criadas via full_supabase_setup.sql)
# echo ">>> Verificando Base de Dados..."
# python migrate_db.py

# 2. Iniciar a aplicação Flask
echo ">>> Iniciando Flask App..."
cd /app
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
