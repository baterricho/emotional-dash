CORE_EMOTIONS = ["Curiosity", "Hope", "Courage", "Strength", "Peace", "Joy", "Acceptance"]


class EmotionSystem:
    def __init__(self, save_data):
        self.save_data = save_data
        self.save_data.setdefault("emotions", [])
        self.save_data.setdefault("stars", 0)
        self.save_data.setdefault("completed_levels", [])

    def discover(self, emotion):
        if emotion and emotion not in self.save_data["emotions"]:
            self.save_data["emotions"].append(emotion)

    def complete_level(self, level_index, emotion, stars=3):
        level_number = int(level_index) + 1
        if level_number not in self.save_data["completed_levels"]:
            self.save_data["completed_levels"].append(level_number)
        self.discover(emotion)
        self.save_data["stars"] = max(self.save_data.get("stars", 0), len(self.save_data["completed_levels"]) * stars)

    def progress_label(self):
        return f"{len(self.save_data['emotions'])}/{len(CORE_EMOTIONS)} emotions"
