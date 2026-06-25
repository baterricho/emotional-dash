import os
import tempfile
import unittest


class LevelAndSettingsSystemsTest(unittest.TestCase):
    def test_level_manager_loads_100_unique_levels(self):
        from src.levels.level_manager import LevelManager

        manager = LevelManager()
        self.assertEqual(manager.total_levels, 100)
        worlds = [manager.get_level(i)["world"] for i in range(100)]
        names = [manager.get_level(i)["name"] for i in range(100)]
        self.assertEqual(len(set(worlds)), 100)
        self.assertEqual(len(set(names)), 100)
        self.assertEqual(manager.get_level(0)["emotion"], "Curiosity")
        self.assertEqual(manager.get_level(99)["name"], "Emotional Balance")

    def test_settings_manager_saves_and_loads_changes(self):
        from src.settings.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            manager = SettingsManager(path)
            self.assertEqual(manager.get("difficulty"), "normal")
            manager.set("difficulty", "relaxed")
            manager.set("focus_mode", True)

            reloaded = SettingsManager(path)
            self.assertEqual(reloaded.get("difficulty"), "relaxed")
            self.assertTrue(reloaded.get("focus_mode"))


if __name__ == "__main__":
    unittest.main()
