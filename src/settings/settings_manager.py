import json
import os
from pathlib import Path


DEFAULT_SETTINGS = {
    "difficulty": "normal",
    "assist_mode": False,
    "auto_dash": False,
    "screen_shake": True,
    "show_tutorial": True,
    "resolution": "1280x720",
    "fullscreen": False,
    "pixel_art_mode": True,
    "particle_quality": "high",
    "background_effects": "high",
    "brightness": 100,
    "visual_effects": True,
    "master_volume": 80,
    "music_volume": 70,
    "sfx_volume": 80,
    "ambient_volume": 70,
    "emotion_music": True,
    "environment_sounds": True,
    "controller_support": True,
    "controller_vibration": True,
    "color_mode": "normal",
    "text_size": "medium",
    "reduce_motion": False,
    "flash_effects": True,
    "subtitles": False,
    "emotion_intensity": "medium",
    "memory_mode": False,
    "focus_mode": False,
    "dream_mode": False,
    "aura": "purple_dream",
    "dash_effect": "shadow_trail",
    "menu_theme": "dream_theme",
    "keybinds": {
        "left": ["a", "left"],
        "right": ["d", "right"],
        "jump": ["space", "up", "w"],
        "dash": ["left shift", "right shift"],
        "skill": ["e"]
    }
}


class SettingsManager:
    def __init__(self, path=None):
        self.path = Path(path or os.path.join(os.getcwd(), "settings.json"))
        self.data = self._load()

    def _load(self):
        data = dict(DEFAULT_SETTINGS)
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    loaded = json.load(f)
                data.update(loaded)
                if isinstance(loaded.get("keybinds"), dict):
                    merged_keys = dict(DEFAULT_SETTINGS["keybinds"])
                    merged_keys.update(loaded["keybinds"])
                    data["keybinds"] = merged_keys
            except (OSError, json.JSONDecodeError):
                pass
        return data

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def toggle(self, key):
        value = not bool(self.data.get(key))
        self.set(key, value)
        return value
