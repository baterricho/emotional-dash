class KeybindManager:
    def __init__(self, settings_manager):
        self.settings = settings_manager

    def bindings_for(self, action):
        return self.settings.get("keybinds", {}).get(action, [])

    def set_binding(self, action, keys):
        keybinds = dict(self.settings.get("keybinds", {}))
        keybinds[action] = list(keys)
        self.settings.set("keybinds", keybinds)
