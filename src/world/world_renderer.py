from .background import palette_from_level
from .effects import weather_for


class WorldRenderer:
    def __init__(self, level_manager):
        self.level_manager = level_manager
        self.level = None

    def load_world(self, index):
        self.level = self.level_manager.get_level(index)
        return self.level

    def draw_background(self):
        return palette_from_level(self.level) if self.level else ((0, 0, 0), (20, 20, 40))

    def draw_decoration(self):
        return self.level.get("decorations", []) if self.level else []

    def draw_particles(self):
        return self.level.get("visual_effects", []) if self.level else []

    def draw_weather(self):
        return weather_for(self.level) if self.level else "none"

    def draw_lighting(self):
        return self.level.get("lighting", "normal") if self.level else "normal"
