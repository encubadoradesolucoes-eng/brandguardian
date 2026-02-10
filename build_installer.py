import PyInstaller.__main__
import sys
import os
import shutil

# Limpar builds anteriores
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

print("Iniciando build do PyInstaller...")

try:
    PyInstaller.__main__.run([
        'BrandGuardianPRO.spec',
        '--clean',
        '--noconfirm'
    ])
    print("Build concluído com sucesso!")
except Exception as e:
    print(f"Erro durante o build: {e}")
    sys.exit(1)
