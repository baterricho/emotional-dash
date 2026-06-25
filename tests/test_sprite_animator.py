import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


class SpriteAnimatorTest(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_splits_sheet_frames_and_advances_animation(self):
        from src.sprite_animator import SpriteAnimator

        sheet = pygame.Surface((16, 8), pygame.SRCALPHA)
        sheet.fill((0, 0, 0, 0))
        sheet.fill((255, 0, 0, 255), pygame.Rect(0, 0, 8, 8))
        sheet.fill((0, 255, 0, 255), pygame.Rect(8, 0, 8, 8))

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            path = tmp.name
        try:
            pygame.image.save(sheet, path)
            animator = SpriteAnimator(
                path,
                {"idle": [(0, 0, 8, 8), (8, 0, 8, 8)]},
                frame_duration=2,
                scale=2,
            )

            self.assertEqual(animator.current_animation, "idle")
            self.assertEqual(animator.current_frame_index, 0)

            animator.update("idle")
            self.assertEqual(animator.current_frame_index, 0)

            animator.update("idle")
            self.assertEqual(animator.current_frame_index, 1)

            target = pygame.Surface((40, 24), pygame.SRCALPHA)
            animator.draw(target, (20, 20), facing=-1)
            self.assertEqual(target.get_at((20, 12)), pygame.Color(0, 255, 0, 255))
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
