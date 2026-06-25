import unittest


class EmotionalAdventureSystemsTest(unittest.TestCase):
    def test_emotion_profiles_change_gameplay_identity(self):
        from src.emotion.emotion_profiles import get_emotion_profile

        fear = get_emotion_profile("Fear")
        anger = get_emotion_profile("Anger")
        hope = get_emotion_profile("Hope")

        self.assertLess(fear["movement"], 1.0)
        self.assertGreater(anger["dash_power"], 1.0)
        self.assertGreaterEqual(hope["extra_jumps"], 1)

    def test_skill_tree_unlocks_from_discovered_emotions(self):
        from src.skills.skill_tree import SkillTree

        tree = SkillTree(["Curiosity", "Hope", "Anger"])
        self.assertTrue(tree.has("double_jump"))
        self.assertTrue(tree.has("healing_dash"))
        self.assertTrue(tree.has("power_dash"))
        self.assertFalse(tree.has("slow_time"))

    def test_major_challenges_appear_every_tenth_level(self):
        from src.levels.level_manager import LevelManager
        from src.world.world_events import WorldEventSystem

        manager = LevelManager()
        bosses = [WorldEventSystem(manager.get_level(i)).challenge_name for i in range(100) if (i + 1) % 10 == 0]
        self.assertEqual(len(bosses), 10)
        self.assertEqual(bosses[-1], "Emotional Core Final Challenge")


if __name__ == "__main__":
    unittest.main()
