"""py2app build script for EVENTRA.

Build with: .venv/bin/python setup.py py2app
"""

from setuptools import setup

APP = ["main.py"]
DATA_FILES = [
    ("database", ["database/schema.sql"]),
]

OPTIONS = {
    "argv_emulation": False,
    "packages": [
        "config",
        "core",
        "controllers",
        "services",
        "repositories",
        "database",
        "models",
        "ui",
        "utils",
        "hardware",
        "customtkinter",
        "cv2",
        "numpy",
        "PIL",
        "qrcode",
        "objc",
        "Foundation",
        "AVFoundation",
        "AppKit",
    ],
    "includes": [
        "tkinter",
        "tkinter.ttk",
        "sqlite3",
        "csv",
        "queue",
        "threading",
    ],
    "excludes": [
        "matplotlib",
        "pytest",
        "unittest",
        "pip",
        "setuptools",
    ],
    "plist": {
        "CFBundleName": "EVENTRA",
        "CFBundleDisplayName": "EVENTRA",
        "CFBundleIdentifier": "com.eventra.desktop",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "11.0",
        "NSCameraUsageDescription": (
            "EVENTRA uses the camera to scan attendee QR tickets during check-in."
        ),
        "NSDesktopFolderUsageDescription": (
            "EVENTRA needs access to its project folder to load app resources."
        ),
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="EVENTRA",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
