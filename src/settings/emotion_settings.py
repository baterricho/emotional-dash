AURA_COLORS = {
    "purple_dream": (166, 88, 255),
    "blue_calm": (80, 170, 255),
    "red_courage": (255, 80, 80),
    "green_hope": (90, 230, 120),
    "gold_balance": (255, 210, 80),
}


class EmotionSettings:
    def __init__(self, settings_manager):
        self.settings = settings_manager

    def aura_color(self):
        return AURA_COLORS.get(self.settings.get("aura"), AURA_COLORS["purple_dream"])

    def intensity_multiplier(self):
        return {"low": 0.55, "medium": 1.0, "high": 1.45}.get(
            self.settings.get("emotion_intensity"), 1.0
        )
