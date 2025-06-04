# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['stackplus.py'],
    pathex=[],
    binaries=[('/Users/brandonnamgoong/Library/Python/3.13/lib/python/site-packages/glfw/libglfw.3.dylib', '.')],
    datas=[('res', 'res')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='stackplus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.icns'],
)
app = BUNDLE(
    exe,
    name='Stack Plus.app',
    icon='icon.icns',
    bundle_identifier=None,
)
