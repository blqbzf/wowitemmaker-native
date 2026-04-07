# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
a = Analysis(
    ['native_app_v5_chinese.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('wowitemmaker-data-dicts.json', '.'),
        ('icon.png', '.'),
        ('conninfo.json', '.'),
    ],
    hiddenimports=[
        'pymysql',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'json',
        'pathlib',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WOWItemMaker',
    debug=False,
    console=False,
    icon='icon.png',
)
