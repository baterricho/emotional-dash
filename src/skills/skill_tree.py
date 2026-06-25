SKILL_UNLOCKS = {
    "Curiosity": "double_jump",
    "Hope": "healing_dash",
    "Courage": "shield",
    "Anger": "power_dash",
    "Calm": "slow_time",
    "Balance": "ultimate_ability",
    "Growth": "ultimate_ability",
    "Acceptance": "skill_weaving",
}


class SkillTree:
    def __init__(self, discovered_emotions=None):
        self.discovered_emotions = set(discovered_emotions or [])

    @property
    def unlocked(self):
        return {
            skill for emotion, skill in SKILL_UNLOCKS.items()
            if emotion in self.discovered_emotions
        }

    def has(self, skill):
        return skill in self.unlocked

    def describe(self):
        if not self.unlocked:
            return "No emotional abilities unlocked yet."
        return ", ".join(sorted(self.unlocked)).replace("_", " ").title()
