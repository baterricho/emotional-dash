# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    ['run.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'levels'),  'levels'),
        (str(ROOT / 'assets'),  'assets'),
        (str(ROOT / 'src'),     'src'),
    ],
    hiddenimports=[
        'numpy',
        'src.emotion.emotion_profiles',
        'src.skills.skill_tree',
        'src.levels.level_manager',
        'src.world.world_events',
        'src.settings.settings_manager',
        'src.story.emotion_system',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

icon_path = str(ROOT / 'assets' / 'icon.ico')

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EmotionArchitect-windows-amd64',
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
    icon=icon_path,
)
