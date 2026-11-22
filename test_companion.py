import unittest
from companion import Companion


class CompanionTests(unittest.TestCase):
    def test_friendship_and_care_remembered_after_restart(self):
        c = Companion(now=100)
        for _ in range(5):
            c.interact('pet')
        c.interact('treat')
        c.interact('catch')
        c.rename('  Nori  ')
        reopened = Companion(c.snapshot(), now=120)
        self.assertEqual(reopened.data['name'], 'Nori')
        self.assertEqual(reopened.data['pets'], 5)
        self.assertEqual(reopened.data['catches'], 1)
        self.assertEqual(reopened.data['treats'], 1)
        self.assertGreater(reopened.data['affection'], 58)
        self.assertEqual(reopened.mood, 'Purring happily')

    def test_focus_completes_once_even_after_restart(self):
        c = Companion(now=100)
        c.start_focus(15, now=100)
        restored = Companion(c.snapshot(), now=200)
        self.assertEqual(restored.remaining(now=200), 800)
        self.assertEqual(restored.tick(now=999), [])
        self.assertEqual(restored.tick(now=1000), ['focus-complete'])
        self.assertEqual(restored.tick(now=1200), [])
        self.assertEqual(restored.data['focus_sessions'], 1)
        self.assertEqual(restored.data['xp'], 20)

    def test_nap_restores_energy_and_absence_is_gentle(self):
        c = Companion({'energy': 30., 'sleeping': True, 'last_updated': 100}, now=100)
        c.tick(now=3700)
        self.assertEqual(c.data['energy'], 50.)
        self.assertEqual(c.mood, 'Dreaming of tiny fish')
        c.data['sleeping'] = False
        c.tick(now=3700 + 86400 * 30)
        self.assertEqual(c.data['energy'], 38.)
        self.assertGreater(c.data['fullness'], 50)

    def test_levels_and_meters_stay_bounded(self):
        c = Companion(now=100)
        for _ in range(20):
            c.interact('cuddle')
            c.interact('treat')
        self.assertGreater(c.level, 1)
        for key in ('affection', 'fullness', 'energy'):
            self.assertLessEqual(c.data[key], 100.)
            self.assertGreaterEqual(c.data[key], 0.)

    def test_invalid_profile_does_not_break_startup(self):
        c = Companion({'xp': 'bad', 'energy': float('nan'), 'name': [], 'focus_until': {}, 'last_updated': float('inf')}, now=100)
        self.assertEqual(c.level, 1)
        self.assertEqual(c.data['energy'], 85.)
        self.assertEqual(c.data['name'], 'Mochi')
        self.assertEqual(c.tick(now=101), [])


if __name__ == '__main__':
    unittest.main()
