# PyInstaller Spec for KEIM (Windows .exe / Ubuntu binary)
# Build: pyinstaller build.spec
# Icon: icon/icon.ico (exe + window title bar)

# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Icon: one 64x64 .ico for EXE and window (see app_icon.py)
_icon_dir = os.path.join(SPECPATH, 'icon')
_icon_64_ico = os.path.join(_icon_dir, 'icon_64.ico')
_datas_icon = [(_icon_64_ico, 'icon')] if os.path.isfile(_icon_64_ico) else []

# Exclude unused packages to reduce size (keep setuptools/distutils - build needs them)
_excludes = [
    'PyQt5', 'PyQt6', 'tkinter',
    'matplotlib', 'mpl_toolkits', 'IPython', 'jupyter', 'nbformat', 'notebook',
    'pytest', '_pytest', 'py', 'pytest_cov', 'pytest_qt',
    'lxml',
    'zmq', 'pyzmq', 'jedi', 'parso', 'prompt_toolkit', 'Pygments',
    'cryptography', 'bcrypt', 'nacl',
    'docutils', 'jinja2', 'sphinx', 'numpydoc',
    'pandas', 'scipy', 'sklearn',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=_datas_icon,
    hiddenimports=[
        'numpy',
        'tifffile',
        'PIL',
        'PIL.Image',
        'h5py',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='keim',
    icon=_icon_64_ico,
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
)
