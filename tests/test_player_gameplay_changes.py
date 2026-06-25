import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


class PlayerGameplayChangesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        import run

        cls.game_mod = run

    def test_level_builder_removes_visible_deadly_spike_platforms(self):
        for idx in range(20):
            platforms, *_ = self.game_mod.build_level(idx)
            visible_spikes = [p for p in platforms if p.visible and p.deadly]
            self.assertEqual(visible_spikes, [], f"world {idx} still has spike hazards")

    def test_player_sprite_uses_70_percent_visual_scale(self):
        self.assertEqual(self.game_mod.PLAYER_VISUAL_SCALE, 0.7)


if __name__ == "__main__":
    unittest.main()
