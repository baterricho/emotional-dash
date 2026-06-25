import json
from pathlib import Path


class LevelLoader:
    def __init__(self, levels_dir=None):
        base_dir = Path(__file__).resolve().parents[2]
        self.levels_dir = Path(levels_dir) if levels_dir else base_dir / "levels"

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
