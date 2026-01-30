#!/bin/bash

# Iniciar o motor WhatsApp em background
echo ">>> Iniciando WhatsApp Engine..."
cd /app/whatsapp-engine
npm install
node server.js &

# Iniciar a aplicação Flask
echo ">>> Iniciando Flask App..."
cd /app
gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
