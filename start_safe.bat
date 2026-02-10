@echo off
TITLE M24 SAFE BOOT
echo ==========================================
echo   INICIANDO M24 (MODO SEGURO)
echo ==========================================

echo 1. Matando processos antigos...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo 2. Iniciando Motor WhatsApp (Janela Separada)...
cd whatsapp-engine
start "WhatsApp" cmd /k "npm start"
cd ..

echo 3. Aguardando 5 segundos...
timeout /t 5 >nul

echo 4. Iniciando Python APP...
:: Tenta ativar venv de varias formas
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

:: Roda o app
python app.py
pause
