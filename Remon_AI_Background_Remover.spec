# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Base packages to collect fully
datas = [
    ('assets', 'assets'),
]

# Include pre-downloaded AI model so the app works 100% offline on any Mac
model_path = os.path.expanduser('~/.rembg/models/bria-rmbg/bria-rmbg.onnx')
if os.path.exists(model_path):
    datas.append((model_path, 'models/bria-rmbg'))

binaries = []
hiddenimports = [
    'numpy',
    'scipy',
    'scipy.ndimage',
    'skimage',
    'skimage.morphology',
    'pymatting',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageOps',
    'bs4',
    'requests',
    'certifi',
    'onnxruntime',
    'onnxruntime.capi',
    'rembg',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

for pkg in ['rembg', 'onnxruntime', 'pymatting', 'skimage']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'notebook'],
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
    name='Remon AI Background Remover Pro V 01.02',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Remon AI Background Remover Pro V 01.02',
)

app = BUNDLE(
    coll,
    name='Remon AI Background Remover Pro V 01.02.app',
    icon='assets/icon.icns',
    bundle_identifier='com.spaceship.remon-ai-background-remover',
    info_plist={
        'CFBundleName': 'Remon AI Background Remover Pro V 01.02',
        'CFBundleDisplayName': 'Remon AI Background Remover Pro V 01.02',
        'CFBundleIdentifier': 'com.spaceship.remon-ai-background-remover',
        'CFBundleVersion': '1.0.2',
        'CFBundleShortVersionString': '1.0.2',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.photography',
        'NSHumanReadableCopyright': 'Copyright © 2026 SpaceShip. All rights reserved.',
    },
)
