# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('whatsapp-engine/*.js', 'whatsapp-engine'),
        ('whatsapp-engine/package.json', 'whatsapp-engine'),
        ('modules', 'modules'),
    ],
    hiddenimports=[
        'flask_sqlalchemy',
        'flask_login',
        'flask_mail',
        'imagehash',
        'PIL',
        'openpyxl',
        'psycopg2',
        'sqlalchemy',
        'blinker',
        'bs4',
        'dotenv',
        'email.mime.text',
        'email.mime.multipart',
        # Fase 1: Monitoramento RPI
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'PyPDF2',
        # Fase 2: Relatórios PDF
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.lib.enums',
        'reportlab.platypus',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['node_modules', 'venv', '.venv'],
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
    console=True, # Deixar console aberto para ver logs de teste inicialmente
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.ico' if os.path.exists('static/favicon.ico') else None,
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
