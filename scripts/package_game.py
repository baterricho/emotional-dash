import platform
import subprocess
import sys
import zipfile
from pathlib import Path

APP_NAME = "EmotionArchitect"
ENTRYPOINT = "run.py"


def platform_tag():
    system = platform.system().lower()
    machine = platform.machine().lower().replace(" ", "")
    if system.startswith("win"):
        os_name = "windows"
    elif system == "darwin":
        os_name = "macos"
    elif system == "linux":
        os_name = "linux"
    else:
        os_name = system
    return f"{os_name}-{machine}"


def sep():
    return ";" if platform.system().lower().startswith("win") else ":"


def main():
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"
    build_name = f"{APP_NAME}-{platform_tag()}"
    ext = ".exe" if platform.system().lower().startswith("win") else ""

    icon_path = root / "assets" / "icon.ico"
    icon_args = ["--icon", str(icon_path)] if icon_path.exists() else []

    # --add-data src:dst  (src = folder on disk, dst = folder inside the exe)
    data_args = [
        "--add-data", f"levels{sep()}levels",
        "--add-data", f"assets{sep()}assets",
        "--add-data", f"src{sep()}src",
    ]

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", build_name,
        "--hidden-import", "numpy",
        "--hidden-import", "src.emotion.emotion_profiles",
        "--hidden-import", "src.skills.skill_tree",
        "--hidden-import", "src.levels.level_manager",
        "--hidden-import", "src.world.world_events",
        "--hidden-import", "src.settings.settings_manager",
        "--hidden-import", "src.story.emotion_system",
        *data_args,
        *icon_args,
        ENTRYPOINT,
    ]
    subprocess.run(command, check=True, cwd=root)

    binary = dist / f"{build_name}{ext}"
    if not binary.exists():
        raise FileNotFoundError(f"Build output not found: {binary}")

    zip_path = root / f"{build_name}.zip"
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(binary, arcname=binary.name)

    print(f"\nCreated binary : {binary}")
    print(f"Created archive: {zip_path}")


if __name__ == "__main__":
    main()
