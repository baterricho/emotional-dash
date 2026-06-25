import os
import tempfile
import unittest


class SettingsInteractionsTest(unittest.TestCase):
    def setUp(self):
        from src.settings.settings_manager import SettingsManager
        from src.settings.interactive_settings import SettingsInteractionModel

        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "settings.json")
        self.manager = SettingsManager(self.path)
        self.model = SettingsInteractionModel(self.manager)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clicking_cycle_arrows_changes_and_saves_value(self):
        control = self.model.controls()[0]
        self.assertEqual(control.key, "difficulty")

        self.model.click(control.right_rect.center)
        self.assertEqual(self.manager.get("difficulty"), "challenge")

        self.model.click(control.left_rect.center)
        self.assertEqual(self.manager.get("difficulty"), "normal")

    def test_toggle_slider_and_choice_controls_save_immediately(self):
        assist = next(c for c in self.model.controls() if c.key == "assist_mode")
        brightness = next(c for c in self.model.controls() if c.key == "brightness")
        aura = next(c for c in self.model.controls() if c.key == "aura")

        self.model.click(assist.value_rect.center)
        self.assertTrue(self.manager.get("assist_mode"))

        self.model.click((brightness.slider_rect.left, brightness.slider_rect.centery))
        self.assertEqual(self.manager.get("brightness"), 0)

        self.model.click(aura.right_rect.center)
        self.assertEqual(self.manager.get("aura"), "blue_calm")

    def test_keybind_capture_updates_primary_binding(self):
        jump = next(c for c in self.model.controls() if c.key == "jump")

        result = self.model.click(jump.value_rect.center)
        self.assertEqual(result["action"], "capture_key")
        self.model.capture_key("k")

        self.assertEqual(self.manager.get("keybinds")["jump"][0], "k")

    def test_reset_progress_requires_confirmation(self):
        reset = next(c for c in self.model.controls() if c.key == "reset_progress")
        save_data = {
            "level": 3,
            "best": 3,
            "coins": 12,
            "cleared": [True, True, False],
            "best_times": [10, 11, 0],
            "completed_levels": [1, 2],
            "stars": 6,
            "emotions": ["Curiosity"],
        }

        result = self.model.click(reset.value_rect.center)
        self.assertEqual(result["action"], "confirm_reset")

        self.model.cancel_reset()
        self.assertFalse(self.model.confirm_reset)
        self.assertEqual(save_data["stars"], 6)

        self.model.click(reset.value_rect.center)
        self.model.confirm_reset_progress(save_data, total_levels=5)
        self.assertEqual(save_data["level"], 0)
        self.assertEqual(save_data["stars"], 0)
        self.assertEqual(save_data["emotions"], [])
        self.assertEqual(save_data["cleared"], [False] * 5)


if __name__ == "__main__":
    unittest.main()
