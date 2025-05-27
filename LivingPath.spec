# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('files', 'files')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('hyperglot')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
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
    name='LivingPath',
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
    icon=['files/logo.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LivingPath',
)
app = BUNDLE(
    coll,
    name='LivingPath.app',
    icon='files/logo.icns',
    bundle_identifier=None,
    version = 1.02,
    info_plist = {
        'NSPrincipalClass': 'NSApplication',
        'CFBundleDocumentTypes': [{
              'CFBundleTypeName': 'LivingPath File',
              'CFBundleTypeIconFile': 'files/logo.icns',
              'LSItemContentTypes': ['public.lvp'],
              'LSHandlerRank': 'Owner'
        }]
    }
)
