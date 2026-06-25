from .level_loader import LevelLoader


class LevelManager:
    def __init__(self, loader=None):
        self.loader = loader or LevelLoader()
        self._levels = self.loader.load_all()
        self._by_number = {level["level"]: level for level in self._levels}

    @property
    def total_levels(self):
        return len(self._levels)

    def get_level(self, index):
        if not self._levels:
            raise ValueError("No level metadata found.")
        number = max(1, min(int(index) + 1, self.total_levels))
        return self._by_number[number]

    def get_world_name(self, index):
        level = self.get_level(index)
        return level.get("world", f"World {index + 1}")

    def get_title(self, index):
        level = self.get_level(index)
        return level.get("name", f"Level {index + 1}")

    def get_story(self, index):
        return self.get_level(index).get("story", "")

    def get_emotion(self, index):
        return self.get_level(index).get("emotion", "Unknown")
