MAJOR_CHALLENGES = {
    10: "Fear Challenge",
    20: "Memory Challenge",
    30: "Shadow Challenge",
    40: "Doubt Challenge",
    50: "Anger Challenge",
    60: "Loss Challenge",
    70: "Freedom Challenge",
    80: "Chaos Challenge",
    90: "Acceptance Challenge",
    100: "Emotional Core Final Challenge",
}


class WorldEventSystem:
    def __init__(self, level):
        self.level = level
        self.level_number = int(level.get("level", 1))
        self.challenge_name = MAJOR_CHALLENGES.get(self.level_number)

    @property
    def has_major_challenge(self):
        return self.challenge_name is not None

    def event_flags(self):
        effects = set(self.level.get("visual_effects", []))
        flags = {
            "rain": "rain" in effects,
            "snow": "snow" in effects,
            "fire": bool({"fire_particles", "embers"} & effects),
            "glitch": "glitch" in effects,
            "fog": bool({"fog", "dark_fog", "soft_fog", "blue_mist"} & effects),
            "falling_objects": self.level_number % 5 == 0,
            "world_transform": self.level_number % 10 == 0,
        }
        return flags

    def intensity(self):
        if self.level.get("difficulty") == "final":
            return 1.6
        if self.level.get("difficulty") == "expert":
            return 1.35
        if self.level.get("difficulty") == "hard":
            return 1.15
        return 1.0
