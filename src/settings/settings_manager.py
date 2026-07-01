import json
import os
from pathlib import Path


SETTINGS_VERSION = 2

DEFAULT_SETTINGS = {
    "settings_version": SETTINGS_VERSION,
    
    # GAMEPLAY
    "difficulty": "normal",
    "assist_mode": False,
    "auto_dash": False,
    "screen_shake": True,
    "tutorial": True,
    "checkpoint_assist": False,
    "game_speed": 100,

    # GRAPHICS
    "fullscreen": False,
    "resolution": "1280x720",
    "pixel_art_mode": True,
    "particle_quality": "high",
    "background_effects": "high",
    "lighting_effects": True,
    "brightness": 100,
    "screen_effects": True,
    "fps_display": False,

    # AUDIO
    "master_volume": 80,
    "music_volume": 70,
    "sfx_volume": 80,
    "ambient_volume": 70,
    "emotion_music": True,
    "environment_sounds": True,
    "mute_all": False,

    # CONTROLS
    "controller_support": True,
    "controller_vibration": True,
    "mouse_sensitivity": 50,
    "key_left": 97,      # pygame.K_a
    "key_right": 100,    # pygame.K_d
    "key_jump": 32,      # pygame.K_SPACE
    "key_dash": 1073742049, # pygame.K_LSHIFT
    "key_skill": 101,    # pygame.K_e  (Shield)
    "key_ghost": 114,   # pygame.K_r  (Ghost Step)
    "key_ultimate": 113,# pygame.K_q  (Ultimate)
    "key_pause": 27,     # pygame.K_ESCAPE
    "key_interact": 13,  # pygame.K_RETURN

    # YOUR JOURNEY
    "emotion_intensity": "medium",
    "aura": "purple_dream",
    "dash_effect": "shadow_trail",
    "focus_mode": False,
    "dream_mode": False,
    "color_theme": "dream_theme",

    # ACCESSIBILITY
    "reduce_motion": False,
    "color_blind_mode": False,
    "high_contrast": False,
    "text_size": "medium",
}


class SettingsManager:
    def __init__(self, path=None):
        self.path = Path(path or os.path.join(os.getcwd(), "settings.json"))
        self._listeners = {}
        self.data = self._load()

    def add_listener(self, event_name, callback):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        if callback not in self._listeners[event_name]:
            self._listeners[event_name].append(callback)

    def remove_listener(self, event_name, callback):
        if event_name in self._listeners and callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)

    def _emit(self, event_name, key, value):
        for callback in self._listeners.get(event_name, []):
            callback(key, value)
        for callback in self._listeners.get("any_setting_changed", []):
            callback(key, value)

    def _load(self):
        data = dict(DEFAULT_SETTINGS)
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    loaded = json.load(f)
                
                # Migration logic
                loaded_version = loaded.get("settings_version", 0)
                if loaded_version < SETTINGS_VERSION:
                    print(f"Migrating settings from version {loaded_version} to {SETTINGS_VERSION}")
                
                # Merge settings
                for k, v in loaded.items():
                    if k in data and isinstance(data[k], dict) and isinstance(v, dict):
                        data[k].update(v)
                    elif k in data:
                        data[k] = v
                        
                data["settings_version"] = SETTINGS_VERSION
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
        if self.data.get(key) != value:
            self.data[key] = value
            self.save()
            self._emit(f"{key}_changed", key, value)

    def toggle(self, key):
        value = not bool(self.data.get(key))
        self.set(key, value)
        return value
