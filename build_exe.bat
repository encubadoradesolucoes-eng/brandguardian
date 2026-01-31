@echo off
title M24 PRO - Gerador de Executavel
color 0B
echo ==========================================
echo   GERANDO EXECUTAVEL BRAND GUARDIAN PRO
echo ==========================================
echo.
echo [*] Limpando pastas antigas...
if exist dist rd /s /q dist
if exist build rd /s /q build

echo [*] Iniciando PyInstaller...
pyinstaller BrandGuardianPRO.spec --noconfirm

echo.
echo [*] Criando atalho de depuracao...
echo @echo off > dist\BrandGuardianPRO\debug_run.bat
echo color 0C >> dist\BrandGuardianPRO\debug_run.bat
echo echo Iniciando em modo de depuracao... >> dist\BrandGuardianPRO\debug_run.bat
echo BrandGuardianPRO.exe >> dist\BrandGuardianPRO\debug_run.bat
echo echo. >> dist\BrandGuardianPRO\debug_run.bat
echo echo O programa parou. Veja o erro acima. >> dist\BrandGuardianPRO\debug_run.bat
echo pause >> dist\BrandGuardianPRO\debug_run.bat

echo.
echo ==========================================
echo   CONCLUIDO! O seu executavel esta em:
echo   dist\BrandGuardianPRO\BrandGuardianPRO.exe
echo.
echo   Se a janela fechar, use o debug_run.bat
echo ==========================================
pause
