class SettingsMenu:
    CATEGORIES = [
        "Gameplay",
        "Graphics",
        "Audio",
        "Controls",
        "Accessibility",
        "Data",
        "Journey",
    ]

    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.category_index = 0

    @property
    def category(self):
        return self.CATEGORIES[self.category_index]

    def next_category(self):
        self.category_index = (self.category_index + 1) % len(self.CATEGORIES)

    def previous_category(self):
        self.category_index = (self.category_index - 1) % len(self.CATEGORIES)
