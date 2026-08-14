# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for a windowed macOS .app / Windows folder build.

Build from the repo root:

    ./build_scripts/macos.sh

The result is output/VulturEklips.app.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

datas: list = []
binaries: list = []
hiddenimports: list[str] = ["piexif"]

_ffmpeg = ROOT / "third_party" / "ffmpeg" / "ffmpeg"
if sys.platform == "win32":
    _win = ROOT / "third_party" / "ffmpeg" / "ffmpeg.exe"
    if _win.is_file():
        _ffmpeg = _win
if _ffmpeg.is_file():
    binaries.append((str(_ffmpeg), "."))
else:
    raise SystemExit(
        "Decode-only ffmpeg is missing. Run build_scripts/build_ffmpeg.sh "
        "before packaging (macos.sh does this automatically)."
    )

# macOS: BUNDLE copies the .icns into Contents/Resources — do not also
# ship it under assets/ (that doubled the icon). Windows/Linux still need
# a loose file for QIcon.
if sys.platform == "darwin":
    APP_ICON = ROOT / "assets" / "app_icon_darwin.icns"
elif sys.platform == "win32":
    APP_ICON = ROOT / "assets" / "app_icon_win.ico"
else:
    APP_ICON = ROOT / "assets" / "app_icon_linux.png"
if APP_ICON.is_file():
    APP_ICON_STR = str(APP_ICON)
    if sys.platform != "darwin":
        datas.append((str(APP_ICON), "assets"))
else:
    APP_ICON_STR = None

# Widgets-only UI. collect_all(PySide6/cv2) pulls WebEngine, QML, Designer, etc.
excludes = [
    "IPython",
    "jupyter",
    "matplotlib",
    "pandas",
    "scipy",
    "tkinter",
    "cv2",
    "imageio_ffmpeg",
    "ssl",
    "_ssl",
    "_hashlib",
    "unittest",
    "pydoc",
    "doctest",
    "xmlrpc",
    "sqlite3",
    "numpy.random",
    "numpy.fft",
    "numpy.f2py",
    "numpy.testing",
    "numpy.distutils",
    "PIL.ImageTk",
    "PIL.ImageCms",
    "PIL.AvifImagePlugin",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPositioning",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtSvg",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.scripts",
]

# Leftover Qt / tooling paths that hooks still copy after module excludes.
_DROP_SUBSTR = (
    "assistant",
    "designer",
    "linguist",
    "lrelease",
    "lupdate",
    "qmlformat",
    "qmlls",
    "qt3d",
    "qtbluetooth",
    "qtcanvaspainter",
    "qtcharts",
    "qtdatavisualization",
    "qtdesigner",
    "qtgraphs",
    "qthelp",
    "qtlocation",
    "qtmultimedia",
    "qtnfc",
    "qtpdf",
    "qtpositioning",
    "qtquick",
    "qtremoteobjects",
    "qtscxml",
    "qtsensors",
    "qtserial",
    "qtshadertools",
    "qtsql",
    "qtsvg",
    "qttest",
    "qttexttospeech",
    "qtuitools",
    "qtvirtualkeyboard",
    "qtwebchannel",
    "qtwebengine",
    "qtwebsockets",
    "qtwebview",
    "/qml/",
    "\\qml\\",
    "/qt/lib/libav",
    "include/",
    "typesystems",
    ".pyi",
    ".qm",
    "/translations/",
    "qtnetwork",
    "libssl",
    "libcrypto",
    "libavif",
    "_avif",
    "_imagingtk",
    "_imagingcms",
    "liblcms2",
    "libqminimal",
    "libqoffscreen",
    "libqgif",
    "libqwbmp",
    "libqtga",
    "libqico",
    "libqmacheif",
    "libqmacjp2",
    "libqsvg",
    "libqicns",
    "libqsvgicon",
    "libqtuiotouch",
    "libqjpeg",
    "libqtiff",
    "libqwebp",
    "numpy/random",
    "numpy/fft",
    "numpy/f2py",
    "numpy/testing",
    "imageio_ffmpeg",
    "_codecs_jp",
    "_codecs_cn",
    "_codecs_hk",
    "_codecs_kr",
    "_codecs_tw",
    "_codecs_iso2022",
)


def _keep_bundle_item(item: tuple) -> bool:
    dest = str(item[0]).replace("\\", "/").lower()
    return not any(token in dest for token in _DROP_SUBSTR)


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "build_scripts" / "pyi_rth_ffmpeg.py")],
    excludes=excludes,
    noarchive=False,
)
a.binaries = [item for item in a.binaries if _keep_bundle_item(item)]
a.datas = [item for item in a.datas if _keep_bundle_item(item)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VulturEklips",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON_STR,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name="VulturEklips",
)

app = BUNDLE(
    coll,
    name="VulturEklips.app",
    icon=APP_ICON_STR,
    bundle_identifier="com.vultureklips.app",
    info_plist={
        "CFBundleDisplayName": "VulturEklips",
        "CFBundleName": "VulturEklips",
        "CFBundleShortVersionString": "0.2.0",
        "NSHighResolutionCapable": True,
    },
)
