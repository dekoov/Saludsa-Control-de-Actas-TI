# -*- mode: python ; coding: utf-8 -*-
import os
import playwright

# Esto evita depender del nombre del entorno virtual (ej. .venv) y hace el build universal.
playwright_path = os.path.dirname(playwright.__file__)
playwright_driver_path = os.path.join(playwright_path, 'driver')

# Definición de rutas relativas (Asumiendo que corres el build desde server-flask/)
icon_path = 'SaludsaActas.ico' # Usa el nombre directo si está en la misma carpeta que el spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../client-react/dist', 'dist'), 
        ('src/infrastructure/documents/templates', 'src/infrastructure/documents/templates'), 
        (playwright_driver_path, 'playwright/driver'),
        ('version.txt', '.'),

    ],
    hiddenimports=['win32com', 'pythoncom', 'docxtpl', 'playwright', 'ldap3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SaludsaActas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SaludsaActas',
)
