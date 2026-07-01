import json
import sys
from pathlib import Path


def _root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


class LevelLoader:
    def __init__(self, levels_dir=None):
        self.levels_dir = Path(levels_dir) if levels_dir else _root() / "levels"

    def load(self, level_number):
        path = self.levels_dir / f"level_{level_number:03d}.json"
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load_all(self):
        levels = []
        for path in sorted(self.levels_dir.glob("level_*.json")):
            with path.open("r", encoding="utf-8") as f:
                levels.append(json.load(f))
        return levels
