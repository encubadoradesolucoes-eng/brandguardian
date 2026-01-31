@echo off
echo ========================================
echo   TESTANDO M24 BRAND GUARDIAN PRO
echo   Executavel Standalone
echo ========================================
echo.

cd dist\BrandGuardianPRO

echo [1/3] Verificando arquivos...
if exist BrandGuardianPRO.exe (
    echo    OK - Executavel encontrado
) else (
    echo    ERRO - Executavel nao encontrado!
    pause
    exit /b 1
)

echo.
echo [2/3] Iniciando aplicacao...
echo    Aguarde... A aplicacao abrira em uma nova janela
echo    Acesse: http://localhost:7000
echo.

start "" BrandGuardianPRO.exe

echo [3/3] Aplicacao iniciada!
echo.
echo ========================================
echo   INSTRUCOES:
echo ========================================
echo   1. Aguarde a janela do console abrir
echo   2. Acesse: http://localhost:7000
echo   3. Login: admin / admin123
echo   4. Teste todas as funcionalidades
echo.
echo   Para parar: Feche a janela do console
echo ========================================
echo.

pause
