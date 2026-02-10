@echo off
color 0A
title M24 BRAND GUARDIAN PRO - START
cls

echo ===================================================
echo   M24 Brand Guardian PRO - v2.0 (Real Intelligence)
echo ===================================================
echo.
echo [1/4] Configurando ambiente...
cd /d "%~dp0"

echo [2/4] Verificando dependencias criticas...
pip install imagehash Pillow requests flask flask-sqlalchemy flask-login colorama > nul 2>&1

echo [3/4] Inicializando banco de dados...
python repair_db.py
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERRO] Falha ao reparar banco de dados!
    pause
    exit /b
)

echo [4/4] Iniciando Servidor M24...
echo.
echo        ACESSE NO NAVEGADOR: http://127.0.0.1:7000
echo.
python app.py
pause
