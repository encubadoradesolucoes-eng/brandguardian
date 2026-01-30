#!/bin/bash

# 1. Criar as tabelas na base de dados (Postgres ou SQLite) automaticamente
echo ">>> Verificando Base de Dados..."
python migrate_db.py

# 2. Iniciar o motor WhatsApp em background
echo ">>> Iniciando WhatsApp Engine..."
cd /app/whatsapp-engine
# npm install já foi feito no Docker build para ser mais rápido
node server.js &

# 3. Iniciar a aplicação Flask
echo ">>> Iniciando Flask App..."
cd /app
gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
