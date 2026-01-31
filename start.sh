#!/bin/bash

# 1. Criar as tabelas na base de dados (Postgres ou SQLite) automaticamente
echo ">>> Verificando Base de Dados..."
python migrate_db.py

# 2. Iniciar o motor WhatsApp em background (Opcional para poupar RAM)
if [ "$DISABLE_WHATSAPP" == "true" ]; then
    echo ">>> WHATSAPP ENGINE DESATIVADO (Modo de Baixa Memoria)"
else
    echo ">>> Iniciando WhatsApp Engine..."
    cd /app/whatsapp-engine
    node server.js &
    cd /app
fi

# 3. Iniciar a aplicação Flask
echo ">>> Iniciando Flask App..."
cd /app
gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
