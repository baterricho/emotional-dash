from dataclasses import dataclass


@dataclass(frozen=True)
class RectSpec:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def center(self):
        return (self.left + self.width // 2, self.top + self.height // 2)

    @property
    def centery(self):
        return self.top + self.height // 2

    def collidepoint(self, point):
        x, y = point
        return self.left <= x <= self.right and self.top <= y <= self.bottom


@dataclass(frozen=True)
class SettingControl:
    category: str
    label: str
    key: str
    kind: str
    rect: RectSpec
    value_rect: RectSpec
    left_rect: RectSpec | None = None
    right_rect: RectSpec | None = None
    slider_rect: RectSpec | None = None
    options: tuple = ()


SETTING_DEFS = [
    ("Gameplay", "Difficulty", "difficulty", "cycle", ("relaxed", "normal", "challenge")),
    ("Gameplay", "Assist Mode", "assist_mode", "toggle", ()),
    ("Gameplay", "Auto Dash", "auto_dash", "toggle", ()),
    ("Gameplay", "Screen Shake", "screen_shake", "toggle", ()),
    ("Gameplay", "Tutorial", "show_tutorial", "toggle", ()),
    ("Graphics", "Pixel Art Mode", "pixel_art_mode", "toggle", ()),
    ("Graphics", "Particle Quality", "particle_quality", "cycle", ("low", "medium", "high")),
    ("Graphics", "Background Effects", "background_effects", "cycle", ("low", "medium", "high")),
    ("Graphics", "Brightness", "brightness", "slider", (0, 100)),
    ("Graphics", "Fullscreen", "fullscreen", "toggle", ()),
    ("Audio", "Master Volume", "master_volume", "slider", (0, 100)),
    ("Audio", "Music Volume", "music_volume", "slider", (0, 100)),
    ("Audio", "Sound Effects Volume", "sfx_volume", "slider", (0, 100)),
    ("Audio", "Ambient Volume", "ambient_volume", "slider", (0, 100)),
    ("Audio", "Emotion Music", "emotion_music", "toggle", ()),
    ("Controls", "Move Left", "left", "keybind", ()),
    ("Controls", "Move Right", "right", "keybind", ()),
    ("Controls", "Jump", "jump", "keybind", ()),
    ("Controls", "Dash", "dash", "keybind", ()),
    ("Controls", "Skill", "skill", "keybind", ()),
    ("Emotional", "Emotion Intensity", "emotion_intensity", "cycle", ("low", "medium", "high")),
    ("Emotional", "Focus Mode", "focus_mode", "toggle", ()),
    ("Emotional", "Dream Mode", "dream_mode", "toggle", ()),
    ("Emotional", "Character Aura", "aura", "cycle", ("purple_dream", "blue_calm", "red_courage", "green_hope", "gold_balance")),
    ("Emotional", "Dash Effect", "dash_effect", "cycle", ("shadow_trail", "star_trail", "heart_energy", "lightning_trail")),
    ("Data", "Reset All Progress", "reset_progress", "danger", ()),
]


class SettingsInteractionModel:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.selected_key = None
        self.capture_action = None
        self.confirm_reset = False

    def controls(self, scroll=0):
        controls = []
        x1, x2 = 190, 720
        y = 160 - int(scroll)
        row_h = 35
        current_category = None
        for category, label, key, kind, options in SETTING_DEFS:
            if category != current_category:
                current_category = category
                y += 30
            rect = RectSpec(x1, y, 900, 30)
            value_rect = RectSpec(x2, y + 2, 270, 26)
            left_rect = RectSpec(x2 - 38, y + 2, 30, 26) if kind == "cycle" else None
            right_rect = RectSpec(x2 + 278, y + 2, 30, 26) if kind == "cycle" else None
            slider_rect = RectSpec(x2, y + 11, 270, 8) if kind == "slider" else None
            controls.append(SettingControl(
                category, label, key, kind, rect, value_rect,
                left_rect, right_rect, slider_rect, tuple(options)
            ))
            y += row_h
        return controls

    def value_label(self, control):
        if control.kind == "toggle":
            return "ON" if self.settings.get(control.key) else "OFF"
        if control.kind == "cycle":
            return str(self.settings.get(control.key)).replace("_", " ").upper()
        if control.kind == "slider":
            return str(int(self.settings.get(control.key, 0)))
        if control.kind == "keybind":
            keys = self.settings.get("keybinds", {}).get(control.key, [])
            return str(keys[0] if keys else "").upper()
        return "RESET"

    def click(self, point, scroll=0):
        for control in self.controls(scroll):
            if control.kind == "cycle":
                if control.left_rect and control.left_rect.collidepoint(point):
                    self._cycle(control, -1)
                    return {"action": "changed", "key": control.key}
                if control.right_rect and control.right_rect.collidepoint(point):
                    self._cycle(control, 1)
                    return {"action": "changed", "key": control.key}
            if control.kind == "slider" and control.slider_rect and control.rect.collidepoint(point):
                self._set_slider(control, point[0])
                return {"action": "changed", "key": control.key}
            if control.value_rect.collidepoint(point) or control.rect.collidepoint(point):
                self.selected_key = control.key
                if control.kind == "toggle":
                    self.settings.toggle(control.key)
                    return {"action": "changed", "key": control.key}
                if control.kind == "cycle":
                    self._cycle(control, 1)
                    return {"action": "changed", "key": control.key}
                if control.kind == "slider":
                    self._set_slider(control, point[0])
                    return {"action": "changed", "key": control.key}
                if control.kind == "keybind":
                    self.capture_action = control.key
                    return {"action": "capture_key", "key": control.key}
                if control.kind == "danger":
                    self.confirm_reset = True
                    return {"action": "confirm_reset"}
        return {"action": "none"}

    def hover_key(self, point, scroll=0):
        for control in self.controls(scroll):
            if control.rect.collidepoint(point):
                return control.key
        return None

    def capture_key(self, key_name):
        if not self.capture_action:
            return False
        keybinds = dict(self.settings.get("keybinds", {}))
        existing = list(keybinds.get(self.capture_action, []))
        tail = [k for k in existing if k != key_name]
        keybinds[self.capture_action] = [key_name] + tail[:1]
        self.settings.set("keybinds", keybinds)
        self.capture_action = None
        return True

    def cancel_reset(self):
        self.confirm_reset = False

    def confirm_reset_progress(self, save_data, total_levels):
        save_data.update({
            "level": 0,
            "best": 0,
            "deaths": 0,
            "runs": 0,
            "coins": 0,
            "cleared": [False] * total_levels,
            "best_times": [0] * total_levels,
            "completed_levels": [],
            "stars": 0,
            "emotions": [],
        })
        self.confirm_reset = False

    def _cycle(self, control, direction):
        values = list(control.options)
        current = self.settings.get(control.key)
        idx = values.index(current) if current in values else 0
        self.settings.set(control.key, values[(idx + direction) % len(values)])

    def _set_slider(self, control, x):
        low, high = control.options
        slider = control.slider_rect
        ratio = 0 if slider.width <= 0 else (x - slider.left) / slider.width
        ratio = max(0.0, min(1.0, ratio))
        self.settings.set(control.key, int(round(low + (high - low) * ratio)))
