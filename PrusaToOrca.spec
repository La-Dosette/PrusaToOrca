# -*- mode: python ; coding: utf-8 -*-
#
# Build recipe for PrusaToOrca. This file is committed on purpose: it is the
# only description of how the published binary is produced, so anyone can read
# it and reproduce the release themselves.
#
# Two deliberate choices, both about antivirus false positives:
#   * onedir, not onefile. A onefile build unpacks itself into %TEMP% and
#     launches a second executable at startup, which is behaviourally identical
#     to a dropper and is what generic ML engines flag.
#   * upx=False. UPX-compressed sections are a strong heuristic signal and buy
#     us nothing here.

from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets'), ('logo.png', '.'), ('logo.ico', '.')]
binaries = []
hiddenimports = []

tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PrusaToOrca',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PrusaToOrca',
)
