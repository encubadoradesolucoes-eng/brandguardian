# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Coletar automaticamente todas as dependencias complexas
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('static/ipi_images', 'static/ipi_images'),
    ('whatsapp-engine/*.js', 'whatsapp-engine'),
    ('whatsapp-engine/package.json', 'whatsapp-engine'),
    ('modules', 'modules')
]
binaries = []
hiddenimports = [
    'flask', 
    'flask.views',
    'flask.signals', 
    'flask_sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.sql.default_comparator',
    'flask_login',
    'flask_mail',
    'flask_migrate',  # Se estiver usando
    'werkzeug.security',
    'werkzeug.utils',
    'werkzeug.exceptions',
    'jinja2.ext',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.application',
    'socket',
    'engineio.async_drivers.threading',  # Para flask-socketio se tiver
    # APScheduler
    'apscheduler.schedulers.background',
    'apscheduler.triggers.cron',
    'apscheduler.executors.pool',
    'tzlocal',
    # ReportLab
    'reportlab.pdfgen.canvas',
    'reportlab.platypus', 
    'reportlab.lib.pagesizes',
    # Outros
    'PIL',
    'imagehash',
    'openpyxl',
    'requests',
    'dotenv',
    'fitz', # PyMuPDF
    'pymupdf'
]

# Coletar dados e dependencias ocultas de pacotes problematicos
pkgs = ['flask', 'flask_sqlalchemy', 'sqlalchemy', 'flask_mail', 'apscheduler', 'reportlab', 'jinja2', 'werkzeug']
for pkg in pkgs:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# Remover duplicatas
hiddenimports = list(set(hiddenimports))

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'tcl', 'dot_env', 'matplotlib', 'IPython'], # Excluir pesados desnecessarios
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BrandGuardianPRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Mantenha True para ver erros no console se houver
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BrandGuardianPRO',
)
