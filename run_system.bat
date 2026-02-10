@echo off
TITLE m24 BrandGuardian - SAFE LAUNCHER
echo ==========================================
echo   INICIANDO M24 PROTECTED MODE
echo ==========================================

:: 1. Limpeza Forçada
echo.
echo [1/3] Limpando processos travados...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

:: 2. Iniciar WhatsApp (em nova janela)
echo.
echo [2/3] Iniciando Motor WhatsApp...
cd whatsapp-engine
start "WhatsApp Engine" cmd /k "npm start"
cd ..

:: 3. Iniciar Python (App Principal)
echo.
echo [3/3] Iniciando Servidor Web...
echo Aguardando 5 segundos para o WhatsApp subir...
timeout /t 5 >nul

:: Tenta ativar venv (sem variaveis complexas para nao dar erro)
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

:: Roda o aplicativo
echo.
echo --- RODANDO APLICATIVO ---
if exist venv\Scripts\python.exe (
	venv\Scripts\python.exe app.py
) else if exist .venv\Scripts\python.exe (
	.venv\Scripts\python.exe app.py
) else (
	python app.py
)

echo.
echo Se o servidor parou, veja o erro acima.
pause
