# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Noise Revenger.

Usage:
    uv run pyinstaller noise_revenger.spec

This spec file creates a single-directory distribution with:
- NoiseRevenger.exe (the main executable)
- config/ and sounds/ directories kept separate for user editing
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'scipy',
        'scipy._lib',
        'scipy.fft',
        'sounddevice',
        'pygame',
        'pygame.mixer',
        'yaml',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

version_file = Path('version_info.txt').resolve()

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NoiseRevenger',
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
    icon=None,
    version=str(version_file) if version_file.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NoiseRevenger',
)
