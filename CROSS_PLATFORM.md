# Cross-Platform Build Guide

## Local build (current OS)

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

2. Build:

```bash
python scripts/package_game.py
```

Output files:
- `dist/EmotionArchitect-<os>-<arch>[.exe]`
- `EmotionArchitect-<os>-<arch>.zip`

## Build all OS targets

Use GitHub Actions workflow:
- `.github/workflows/build-cross-platform.yml`

It builds on:
- Windows
- Linux
- macOS

and uploads zipped artifacts for each platform.

## Save file location

Game save now uses a user-data directory per OS:
- Windows: `%APPDATA%\\EmotionArchitect\\ea_v5.json`
- macOS: `~/Library/Application Support/EmotionArchitect/ea_v5.json`
- Linux: `$XDG_DATA_HOME/EmotionArchitect/ea_v5.json` or `~/.local/share/EmotionArchitect/ea_v5.json`
