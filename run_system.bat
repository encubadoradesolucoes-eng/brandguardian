@echo off
title BrandGuardian Launcher
color 0A

echo ==================================================
echo   BRAND GUARDIAN PRO - SYSTEM LAUNCHER
echo ==================================================
echo.

echo [0/2] Limpando processos antigos...
:: Mata processos Node e Python antigos para liberar portas 3002 e 7000
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
echo Limpeza concluida.

echo.
echo [1/2] Verificando Motor WhatsApp...
echo Iniciando servico Node.js na porta 3002 em nova janela...
cd whatsapp-engine
if not exist node_modules (
    echo [!] Instalando dependencias do Node... esta primeira vez pode demorar...
    call npm install
)
start "BrandGuardian WhatsApp Engine" cmd /k "npm start"
cd ..

echo.
echo [2/2] Aguardando Motor WhatsApp iniciar (5s)...
timeout /t 5 >nul

echo.
echo [3/2] Iniciando Aplicacao Web (Python Flask)...
echo.

if not exist .venv (
    echo [ERRO] Ambiente virtual .venv nao encontrado!
    pause
    exit
)

call .venv\Scripts\activate
python app.py

pause
