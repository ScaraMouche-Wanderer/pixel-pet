import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QSystemTrayIcon, QWidget
from animals import ACTIVITIES, EXTRA_ANIMATIONS, FLYERS, Outing
from bubbles import bubble_position, fit_text, theme_for
from pet_moves import MOVES
from companion import voice_for
from pet import Settings, Sprites, Pet, PETS, ROWS


class PetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'XDG_CONFIG_HOME': self.temp.name})
        self.env.start()
        self.settings = Settings(Path(self.temp.name) / 'settings.json')
        self.pet = Pet(self.settings, preview=True)
        self.pet.ticker.stop()

    def tearDown(self):
        self.pet.tray.hide()
        self.pet.close()
        self.pet.effects.close()
        self.pet.ball.close()
        self.pet.firefly.close()
        self.pet.card.close()
        self.pet.deleteLater()
        self.app.processEvents()
        self.env.stop()
        self.temp.cleanup()

    def test_all_original_sheets_have_nonempty_frames(self):
        for pet in PETS:
            sprites = Sprites(pet, 128)
            for mode, (row, durations) in sprites.animations.items():
                for column in range(len(durations)):
                    frame = sprites.frame(row, column)
                    self.assertFalse(frame.isNull(), (pet, mode, column))
                    self.assertFalse(sprites.masks[row, column].isEmpty(), (pet, mode, column))
                    if sprites.is_cat:
                        self.assertFalse(sprites.masks[row, column].contains(QPoint(0, 0)), (pet, mode, column))
            for row in ((9, 10) if sprites.has_look else ()):
                for column in range(8):
                    sprites.frame(row, column)
                    self.assertFalse(sprites.masks[row, column].isEmpty(), (pet, row, column))

    @unittest.skipUnless('codex' in PETS, 'Optional local sprite sheet')
    def test_frame_timings_match_idle_and_wave(self):
        p = self.pet
        p.select_pet('codex')
        p.mode_until = 100
        far = QPoint(-10000, -10000)
        self.assertEqual(p.frame_at(100.0, far), (0, 0))
        self.assertEqual(p.frame_at(101.7, far), (0, 1))
        self.assertEqual(p.frame_at(103.1, far), (0, 3))
        p.mode, p.mode_started, p.mode_until = 'waving', 100, 103
        self.assertEqual(p.frame_at(100.15, far), (3, 1))
        self.assertEqual(p.frame_at(100.45, far), (3, 3))

    @unittest.skipUnless('codex' in PETS, 'Optional local sprite sheet')
    def test_original_sixteen_look_directions(self):
        import math
        p = self.pet
        p.select_pet('codex')
        p.mode_until = 100
        c = p.geometry().center()
        for index in range(16):
            a = math.radians(index * 22.5)
            point = c + QPoint(round(math.sin(a) * 150), round(-math.cos(a) * 150))
            self.assertEqual(p.frame_at(100.5, point), (9 + index // 8, index % 8))

    def test_right_click_opens_compact_menu_and_show_menu_reuses_a_standalone_window(self):
        p = self.pet
        QTest.mouseClick(p, Qt.RightButton, pos=QPoint(60, 60))
        quick = p.quick_menu
        self.assertTrue(quick.isVisible())
        self.assertFalse(quick.isModal())
        self.assertIs(quick.parentWidget(), p)
        self.assertIs(quick.windowHandle().transientParent(), p.windowHandle())
        self.assertEqual(quick.windowType(), Qt.Dialog)
        self.assertIsNone(QApplication.activePopupWidget())
        self.assertEqual([quick.hide_button.text(), quick.show_button.text()], ['Hide', 'Show menu'])
        QTest.mouseClick(quick.show_button, Qt.LeftButton)
        self.app.processEvents()
        self.assertFalse(quick.isVisible())
        self.assertIsNone(QApplication.activePopupWidget())
        controls = p.controls
        self.assertTrue(controls.isVisible())
        self.assertFalse(controls.isModal())
        self.assertIs(controls.parentWidget(), p)
        self.assertIs(controls.windowHandle().transientParent(), p.windowHandle())
        self.assertEqual(controls.windowType(), Qt.Dialog)
        self.assertEqual(controls.minimumSize(), controls.maximumSize())
        self.assertEqual(controls.tabs.count(), 3)
        QTest.keyClick(controls, Qt.Key_Escape)
        self.assertFalse(controls.isVisible())
        self.assertTrue(p.isVisible())
        p.open_controls()
        self.assertIs(p.controls, controls)
        self.assertTrue(controls.isVisible())
        self.assertFalse(controls.isMaximized())

    def test_menus_dismiss_when_focus_moves_to_another_window(self):
        p = self.pet
        other = QWidget()
        try:
            for name, open_menu in (('quick_menu', lambda: p.open_pet_menu(p.geometry().center())),
                                    ('controls', p.open_controls)):
                with self.subTest(menu=name):
                    open_menu()
                    QTest.qWait(25)
                    menu = getattr(p, name)
                    self.assertTrue(menu.isActiveWindow())
                    other.show()
                    other.activateWindow()
                    QTest.qWait(25)
                    self.assertTrue(other.isActiveWindow())
                    self.assertFalse(menu.isVisible())
                    open_menu()
                    QTest.qWait(25)
                    self.assertTrue(menu.isActiveWindow())
                    menu.close()
        finally:
            other.close()

    def test_controls_change_appearance_and_save_without_closing(self):
        p = self.pet
        p.open_controls()
        page = p.controls.appearance
        self.assertEqual(set(page.pet_buttons), set(PETS))
        for button in (page.pet_buttons['eagle'], page.colour_buttons['pastel'],
                       page.size_buttons[192], page.pace_buttons['zoomies']):
            QTest.mouseClick(button, Qt.LeftButton)
            self.assertTrue(button.isChecked())
            self.assertTrue(p.controls.isVisible())
        data = Settings(self.settings.path).data
        self.assertEqual((data['pet'], data['style'], data['size'], data['play_pace']),
                         ('eagle', 'pastel', 192, 'zoomies'))

    def test_hover_and_left_click_keep_quick_menu_closed(self):
        p = self.pet
        point = p.mask().boundingRect().center()
        QTest.mouseMove(p, point)
        QTest.qWait(QApplication.doubleClickInterval() + 50)
        self.assertIsNone(p.quick_menu)
        QTest.mouseClick(p, Qt.LeftButton, pos=point)
        QTest.qWait(QApplication.doubleClickInterval() + 50)
        self.assertIsNone(p.quick_menu)

    def test_exclusive_moves_run_from_play_menu_for_every_installed_pet(self):
        pet = self.pet
        pet.settings.data.update(autonomous=False, roam=False, motion_effects=True)
        for species in PETS:
            pet.select_pet(species)
            for index, move in enumerate(MOVES[species]):
                with self.subTest(species=species, move=move.name):
                    pet.open_controls()
                    button = pet.controls.play.move_buttons[index]
                    self.assertEqual(button.text(), move.name)
                    button.click()
                    self.assertEqual(pet.mode, move.pose)
                    props = [item for item in pet.effects.particles if 'path' in item]
                    self.assertEqual([item['kind'] for item in props], [move.prop] * move.count)
                    pet.effects.tick(.2)
                    self.assertFalse(pet.effects.grab().isNull())
        self.assertEqual(pet.companion.data['xp'], 0)

    @unittest.skipUnless('seedy' in PETS, 'Optional Seedy sprite is not installed')
    def test_seedy_drops_leaves_and_fruit_autonomously(self):
        pet = self.pet
        pet.select_pet('seedy')
        pet.settings.data.update(roam=False, autonomous=True, motion_effects=True)
        pet.move_queue = list(reversed(MOVES['seedy'][:2]))
        for move in MOVES['seedy'][:2]:
            pet.last_interaction = pet.mode_until = pet.next_pet_move = 0
            pet.tick()
            prop = pet.effects.particles[0]
            self.assertEqual(prop['kind'], move.prop)
            initial_y = prop['y']
            pet.effects.tick(1)
            self.assertGreater(prop['y'], initial_y)
            pet.effects.clear()
        pet.settings.data['autonomous'] = False
        pet.mode_until = pet.next_pet_move = 0
        pet.tick()
        self.assertFalse(pet.effects.particles)

    def test_exclusive_moves_cycle_automatically_with_zoo_open(self):
        pet = self.pet
        pet.select_pet('cat')
        pet.settings.data.update(autonomous=True, roam=False, motion_effects=True)
        pet.open_controls()
        seen = []
        for _ in MOVES['cat']:
            pet.last_interaction = pet.next_pet_move = 0
            pet.tick()
            seen.append(pet.effects.particles[0]['kind'])
        self.assertCountEqual(seen, [move.prop for move in MOVES['cat']])
        pet.controls.findChild(QPushButton, 'closeZoo').click()
        self.assertFalse(pet.controls.isVisible())
        self.assertFalse(pet.controls.pointer_watch.isActive())

    def test_double_click_jumps_without_opening_a_menu(self):
        p = self.pet
        QTest.mouseClick(p, Qt.LeftButton, pos=QPoint(60, 60))
        QTest.mouseDClick(p, Qt.LeftButton, pos=QPoint(60, 60))
        self.assertEqual(p.mode, 'jumping')
        self.assertIsNone(p.drag_origin)
        QTest.qWait(QApplication.doubleClickInterval() + 50)
        self.assertIsNone(p.quick_menu)

    def test_hide_stops_play_and_focus_can_finish_before_tray_restore(self):
        p = self.pet
        p.start_fireflies()
        self.assertTrue(p.firefly.isVisible())
        QTest.mouseClick(p, Qt.RightButton, pos=QPoint(60, 60))
        quick = p.quick_menu
        self.assertTrue(quick.isVisible())
        QTest.mouseClick(quick.hide_button, Qt.LeftButton)
        self.assertFalse(quick.isVisible())
        self.assertFalse(any(widget.isVisible() for widget in (p, p.effects, p.ball, p.firefly, p.card)))
        self.assertFalse(p.firefly.active)
        self.assertEqual([action.text() for action in p.tray_menu.actions() if action.isVisible()],
                         ['Show pet', 'Bring pet home', 'Quit'])

        p.preview = False
        p.companion.start_focus(15, now=time.time() - 901)
        p.last_model_tick = 0
        with patch('pet.subprocess.Popen'):
            p.tick()
        self.assertEqual(p.companion.data['focus_sessions'], 1)
        self.assertFalse(p.isVisible())
        self.assertFalse(p.effects.isVisible())
        p.tray_clicked(QSystemTrayIcon.Trigger)
        self.assertTrue(p.isVisible())
        self.assertIn('Show menu', [action.text() for action in p.tray_menu.actions() if action.isVisible()])

    def test_pet_size_pause_and_settings_persist(self):
        p = self.pet
        p.select_pet('eagle')
        p.resize_pet(96)
        p.toggle('paused')
        saved = Settings(self.settings.path)
        self.assertEqual(saved.data['pet'], 'eagle')
        self.assertEqual(saved.data['size'], 96)
        self.assertTrue(saved.data['paused'])
        self.assertEqual(p.frame_at(time.monotonic(), QPoint()), (0, 0))
        self.assertEqual(saved.path.stat().st_mode & 0o777, 0o600)

    def test_window_layer_toggle_preserves_position_and_updates_all_surfaces(self):
        p = self.pet
        self.settings.path.write_text('{"companion": {"name": "Nori", "xp": 64}}')
        self.assertFalse(Settings(self.settings.path).data['always_on_top'])
        p.show()
        p.start_fireflies()
        surfaces = (p, p.effects, p.ball, p.firefly, p.card)
        points = [widget.pos() for widget in surfaces]
        visibility = [widget.isVisible() for widget in surfaces]
        self.assertTrue(p.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop))
        self.assertTrue(all(widget.windowFlags() & Qt.WindowStaysOnBottomHint for widget in surfaces))
        p.open_controls()
        option = p.controls.options.toggles['always_on_top']
        self.assertFalse(option.isChecked())
        option.click()
        self.assertTrue(p.controls.isVisible())
        self.assertTrue(Settings(self.settings.path).data['always_on_top'])
        self.assertTrue(all(widget.windowFlags() & Qt.WindowStaysOnTopHint for widget in surfaces))
        self.assertFalse(any(widget.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop) for widget in surfaces))
        self.assertEqual([widget.pos() for widget in surfaces], points)
        self.assertEqual([widget.isVisible() for widget in surfaces], visibility)
        self.assertTrue(p.firefly.active)
        option.click()
        self.assertFalse(Settings(self.settings.path).data['always_on_top'])
        self.assertTrue(p.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop))
        self.assertFalse(p.card.testAttribute(Qt.WA_X11NetWmWindowTypeDesktop))

    def test_animal_styles_swap_art_and_remember_the_selections(self):
        p = self.pet
        for animal in ('cat', 'monkey', 'eagle'):
            p.select_pet(animal)
            p.select_style('original')
            image, mask = p.sprites.frame(0, 0).toImage(), p.mask()
            p.select_style('pastel')
            self.assertNotEqual(image, p.sprites.frame(0, 0).toImage())
            self.assertEqual(mask, p.mask())
            self.assertEqual(p.card.avatar_pet, (animal, 'pastel'))
            self.assertEqual(Settings(self.settings.path).data['pet'], animal)
            self.assertEqual(Settings(self.settings.path).data['style'], 'pastel')

    def test_monkey_chooses_an_edge_climbs_and_returns_by_itself(self):
        p = self.pet
        p.select_pet('monkey')
        p.show()
        origin = p.pos()
        clock = [time.monotonic()]
        p.next_outing = clock[0]
        p.last_interaction = clock[0] - 10
        with patch('time.monotonic', side_effect=lambda: clock[0]), patch.object(p, 'underMouse', return_value=True):
            p.tick()
            route = p.outing
            self.assertIsNotNone(route)
            clock[0] += route.legs[0][1] + route.legs[1][1] / 2
            p.tick()
            self.assertIn(p.mode, ('trick-left', 'trick-right'))
            self.assertEqual(p.x(), route.legs[0][0].x())
            self.assertLess(p.y(), route.legs[0][0].y())
            self.assertTrue(p.screen().availableGeometry().contains(p.geometry()))
            clock[0] = route.started + route.duration + .1
            p.tick()
        self.assertEqual(p.pos(), origin)
        self.assertIsNone(p.outing)

    def test_animals_have_distinct_card_text_names_and_treat_reactions(self):
        p = self.pet
        seen = set()
        for animal, treat, trick, name in (
                ('cat', 'Fish treat', 'Chase yarn', 'Mochi'),
                ('monkey', 'Banana slice', 'Climb an edge', 'Pip'),
                ('eagle', 'River fish', 'Take flight', 'Skye')):
            p.select_pet(animal)
            self.assertEqual(p.card.name.text(), name)
            self.assertEqual(p.card.treat_button.text(), treat)
            self.assertEqual(p.card.trick_button.text(), trick)
            self.assertNotIn(p.card.mood.text(), seen)
            seen.add(p.card.mood.text())
            p.interact('treat')
            self.assertEqual(p.effects.message, p.voice['treat'])
        self.assertEqual(Settings(p.settings.path).data['pet_names']['monkey'], 'Pip')

    def test_every_selectable_pet_has_its_own_bubble_lines(self):
        for moment in ('hello', 'pet', 'treat', 'cuddle', 'jump', 'nap', 'wake', 'idle',
                       'focus', 'follow', 'rename', 'finish'):
            with self.subTest(moment=moment):
                lines = [voice_for(pet)[moment] for pet in PETS]
                self.assertEqual(len(set(lines)), len(PETS))

    def test_owl_keeps_its_head_pat_line_on_level_up_and_switching_replaces_it(self):
        pet = self.pet
        pet.select_pet('owl')
        pet.companion.data['xp'] = 28
        pet.interact('pet')
        self.assertTrue(pet.effects.message.startswith('Soft feathers make good company.'))
        self.assertIn('Friendship level 2', pet.effects.message)
        pet.select_pet('cat-classic')
        self.assertEqual(pet.effects.message, '')
        pet.interact('pet')
        self.assertEqual(pet.effects.message, 'Yes, under the chin please.')

    def test_autonomous_routes_need_no_scenery_window(self):
        p = self.pet
        p.select_pet('monkey')
        p.show()
        p.perform_trick(time.monotonic(), automatic=True)
        self.assertIsNotNone(p.outing)
        self.assertFalse(any(w.windowTitle() == 'Pixel Pet Playfield'
                             for w in self.app.topLevelWidgets()))
        p.toggle('autonomous')
        self.assertIsNone(p.outing)
        self.assertTrue(p.roaming_area.contains(p.geometry()))

    def test_auto_activity_cycles_vary_and_do_not_repeat_back_to_back(self):
        p = self.pet
        for pet, activities in ACTIVITIES.items():
            if pet not in PETS:
                continue
            p.select_pet(pet)
            choices = [p.next_activity(pet) for _ in range(5 * len(activities))]
            self.assertEqual(choices[0], activities[0])
            self.assertTrue(all(a != b for a, b in zip(choices, choices[1:])))
            for i in range(0, len(choices), len(activities)):
                self.assertCountEqual(choices[i:i + len(activities)], activities)

    def test_route_height_and_pace_vary_for_same_activity(self):
        p = self.pet
        areas = [Outing('swoop', p.geometry(), p.roaming_area, 0) for _ in range(6)]
        lengths = {round(route.duration, 3) for route in areas}
        heights = {route.legs[0][0].y() for route in areas}
        self.assertGreater(len(lengths), 1)
        self.assertGreater(len(heights), 1)

    def test_showtime_button_runs_distinct_bounded_routines_without_awarding_xp(self):
        pet = self.pet
        for animal, action_label, motion in (
                ('cat', 'Comet pounce', 'jumping'), ('monkey', 'Cartwheel dash', 'stunt-'),
                ('eagle', 'Sky corkscrew', 'stunt-')):
            pet.select_pet(animal)
            pet.card.open_card()
            self.assertIn(action_label, pet.card.showtime_button.text())
            QTest.mouseClick(pet.card.showtime_button, Qt.LeftButton)
            self.assertFalse(pet.card.isVisible())
            route = pet.outing
            self.assertEqual(route.activity, animal + '-show')
            self.assertTrue(any(mode.startswith(motion) for _, _, mode in route.legs))
            positions = set()
            for step in range(1, 21):
                point, _ = route.sample(route.started + route.duration * step / 21)
                self.assertTrue(pet.screen().availableGeometry().contains(QRect(point, pet.size())))
                positions.add((point.x(), point.y()))
            self.assertGreater(len(positions), 5)
            pet.advance_outing(route.started + route.duration + .01)
            self.assertIsNone(pet.outing)
            self.assertEqual(pet.pos(), route.origin)
            self.assertEqual(pet.companion.data['xp'], 0)

    def test_motion_marks_are_world_anchored_and_can_be_switched_off(self):
        pet = self.pet
        pet.select_pet('eagle')
        pet.effects.leave_motion_marks(pet.pos(), QPoint(4, 1), airborne=True)
        before = [(item['x'], item['y']) for item in pet.effects.particles]
        self.assertTrue(all(item['kind'] == 'feather' for item in pet.effects.particles))
        pet.move(pet.pos() - QPoint(30, 0))
        pet.effects.tick(0.)
        self.assertEqual(before, [(item['x'], item['y']) for item in pet.effects.particles])
        self.assertTrue(pet.effects.windowFlags() & Qt.WindowTransparentForInput)
        pet.toggle('motion_effects')
        self.assertFalse(pet.effects.particles)
        self.assertFalse(Settings(pet.settings.path).data['motion_effects'])

    def test_play_pace_and_focus_rules_apply_to_showtime(self):
        pet = self.pet
        pet.set_play_pace('gentle')
        pet.start_showtime()
        gentle_duration = pet.outing.duration
        pet.set_play_pace('zoomies')
        pet.start_showtime()
        self.assertLess(pet.outing.duration, gentle_duration)
        self.assertEqual(Settings(pet.settings.path).data['play_pace'], 'zoomies')
        pet.start_focus(15)
        pet.start_showtime()
        self.assertIsNone(pet.outing)
        self.assertFalse(pet.card.showtime_button.isEnabled())

    def test_eagle_flies_and_toys_interrupt_the_outing(self):
        p = self.pet
        p.select_pet('eagle')
        p.show()
        origin = p.pos()
        now = time.monotonic()
        p.perform_trick(now)
        route = p.outing
        p.advance_outing(now + route.legs[0][1] + route.legs[1][1] / 2)
        self.assertLess(p.y(), origin.y())
        self.assertTrue(p.mode.startswith('trick-'))
        p.start_fireflies()
        self.assertIsNone(p.outing)
        self.assertTrue(p.firefly.active)
        self.assertEqual(p.pos(), origin)
        p.start_focus(15)
        p.perform_trick(now)
        self.assertIsNone(p.outing)
        self.assertEqual(p.frame_at(now, QPoint()), (0, 3))

    def test_both_birds_take_off_fly_and_land_on_the_same_screen(self):
        p = self.pet
        for bird in (key for key in FLYERS if key in PETS):
            with self.subTest(bird=bird):
                p.select_pet(bird)
                p.home()
                screen = p.screen().availableGeometry()
                origin = p.pos()
                p.open_controls()
                p.controls.play.trick.click()
                route = p.outing
                self.assertEqual(route.activity, bird + '-flight')
                frames = [route.sample(route.started + route.duration * i / 80) for i in range(81)]
                self.assertTrue(all(screen.contains(QRect(point, p.size())) for point, _ in frames))
                self.assertGreater(max(abs(point.x() - origin.x()) for point, _ in frames), 200)
                self.assertGreater(max(origin.y() - point.y() for point, _ in frames), 80)
                for phase in ('takeoff', 'glide' if bird == 'eagle' else 'flap', 'land'):
                    self.assertTrue(any(mode and mode.startswith(f'trick-{phase}') for _, mode in frames))
                self.assertEqual(frames[-1][0], origin)
                p.advance_outing(route.started + route.duration + .01)
                self.assertIsNone(p.outing)
                self.assertEqual(p.pos(), origin)

    def test_each_animal_has_visible_additional_poses(self):
        p = self.pet
        for animal in ('cat', 'cat-classic', 'monkey', *(bird for bird in FLYERS if bird in PETS)):
            p.select_pet(animal)
            self.assertTrue(EXTRA_ANIMATIONS[p.animal])
            for mode, _ in EXTRA_ANIMATIONS[p.animal]:
                row, _ = p.sprites.animations[mode]
                self.assertNotEqual(p.sprites.frame(row, 1).toImage(), p.sprites.frame(row, 2).toImage(),
                                    (animal, mode))

    def test_cat_autonomous_yarn_catch_does_not_change_friendship_progress(self):
        p = self.pet
        clock = [time.monotonic()]
        p.next_outing = clock[0]
        p.last_interaction = clock[0] - 10
        with patch('time.monotonic', side_effect=lambda: clock[0]), patch.object(p, 'underMouse', return_value=False):
            p.tick()
            self.assertTrue(p.ball.active and p.ball.quiet)
            for _ in range(600):
                clock[0] += .04
                p.tick()
                if not p.ball.active:
                    break
        self.assertFalse(p.ball.active)
        self.assertEqual(p.mode, 'jumping')
        self.assertEqual(p.companion.data['xp'], 0)
        self.assertEqual(p.companion.data['catches'], 0)

    def test_autostart_opt_in_and_remove(self):
        p = self.pet
        self.assertFalse(p.autostart_path.exists())
        p.set_autostart(True)
        desktop_entry = p.autostart_path.read_text()
        self.assertIn(f'"{Path(__file__).with_name("pet.py")}"', desktop_entry)
        self.assertIn('Name=Pixel Pet', desktop_entry)
        p.set_autostart(False)
        self.assertFalse(p.autostart_path.exists())

    def test_invalid_settings_recover(self):
        self.settings.path.write_text('{broken')
        self.assertEqual(Settings(self.settings.path).data['pet'], 'cat')
        self.settings.path.write_text('{"pet":"missing","size":999,"position":["bad",3]}')
        recovered = Settings(self.settings.path)
        self.assertEqual(recovered.data['size'], 160)
        self.assertIsNone(recovered.data['position'])

    def test_size_upgrade_keeps_progress_and_later_size_choices(self):
        import json
        self.settings.path.write_text(json.dumps({'pet': 'cat', 'size': 128,
                                                 'companion': {'name': 'Nori', 'xp': 64}}))
        upgraded = Settings(self.settings.path)
        self.assertEqual(upgraded.data['size'], 160)
        self.assertEqual(upgraded.data['companion'], {'name': 'Nori', 'xp': 64})
        upgraded.data['size'] = 128
        upgraded.save()
        self.assertEqual(Settings(upgraded.path).data['size'], 128)

    def test_hold_to_cuddle_without_extra_single_click(self):
        p = self.pet
        QTest.mousePress(p, Qt.LeftButton, pos=QPoint(60, 60))
        QTest.qWait(760)
        QTest.mouseRelease(p, Qt.LeftButton, pos=QPoint(60, 60))
        QTest.qWait(QApplication.doubleClickInterval() + 40)
        self.assertEqual(p.companion.data['xp'], 4)
        self.assertEqual(p.companion.data['pets'], 0)
        self.assertTrue(p.effects.particles)
        self.assertIsNone(p.quick_menu)

    def test_treat_pet_name_and_bond_survive_restart(self):
        p = self.pet
        p.companion.rename('Nori')
        p.interact('pet')
        p.interact('treat')
        saved = Settings(self.settings.path).data['companion']
        self.assertEqual(saved['name'], 'Nori')
        self.assertEqual(saved['pets'], 1)
        self.assertEqual(saved['treats'], 1)
        self.assertEqual(saved['fullness'], 100.)

    def test_focus_freezes_chase_and_finishes_without_notification_in_preview(self):
        p = self.pet
        p.start_yarn()
        p.follow_until = time.monotonic() + 10
        p.start_focus(15)
        self.assertFalse(p.ball.active)
        self.assertEqual(p.follow_until, 0)
        self.assertEqual(p.frame_at(time.monotonic(), QPoint()), (0, 2))
        p.companion.data['focus_until'] = time.time() - 1
        p.last_model_tick = 0
        with patch('pet.subprocess.Popen') as spawn:
            p.tick()
            p.last_model_tick = 0
            p.tick()
        spawn.assert_not_called()
        self.assertEqual(p.companion.data['focus_sessions'], 1)
        self.assertEqual(p.companion.data['xp'], 20)

    def test_yarn_chase_can_catch_after_real_physics_steps(self):
        p = self.pet
        clock = [1000.]
        with patch('time.monotonic', side_effect=lambda: clock[0]):
            p.last_tick = clock[0]
            p.start_yarn()
            for _ in range(600):
                clock[0] += .04
                p.tick()
                if not p.ball.active:
                    break
        self.assertFalse(p.ball.active)
        self.assertEqual(p.companion.data['catches'], 1)
        self.assertEqual(p.companion.data['xp'], 6)

    def test_held_yarn_does_not_auto_catch(self):
        p = self.pet
        p.start_yarn()
        p.ball.started = time.monotonic() - 5
        p.ball.dragging = True
        p.ball.move(p.pos())
        p.ball.tick(.04)
        self.assertTrue(p.ball.active)
        self.assertEqual(p.companion.data['catches'], 0)

    def test_middle_click_opens_compact_card(self):
        p = self.pet
        QTest.mouseClick(p, Qt.MiddleButton, pos=QPoint(60, 60))
        self.assertTrue(p.card.isVisible())
        self.assertLessEqual(p.card.height(), 430)
        QTest.keyClick(p.card, Qt.Key_Escape)
        self.assertFalse(p.card.isVisible())

    def test_firefly_hunt_from_card_stays_in_bounds_and_rewards_once(self):
        p = self.pet
        p.show()
        p.card.open_card()
        QTest.mouseClick(p.card.findChild(QPushButton, 'fireflies'), Qt.LeftButton)
        self.assertFalse(p.card.isVisible())
        self.assertTrue(p.firefly.isVisible())
        screen = p.screen().availableGeometry()
        for _ in range(p.firefly.target_count):
            point = p.firefly.pos()
            self.assertTrue(screen.contains(p.firefly.geometry()))
            self.assertFalse(p.firefly.geometry().intersects(p.geometry()))
            QTest.mouseClick(p.firefly, Qt.LeftButton, pos=p.firefly.rect().center())
            if p.firefly.active:
                self.assertNotEqual(p.firefly.pos(), point)
        QTest.mouseClick(p.firefly, Qt.LeftButton, pos=p.firefly.rect().center())
        self.assertFalse(p.firefly.isVisible())
        saved = Settings(self.settings.path).data['companion']
        self.assertEqual(saved['firefly_rounds'], 1)
        self.assertEqual(saved['xp'], 12)
        self.assertIn('Hunts won 1', p.card.record.text())

    def test_firefly_deadline_and_other_activities_cancel_the_round(self):
        p = self.pet
        p.start_yarn()
        p.start_fireflies()
        self.assertFalse(p.ball.active)
        p.firefly.deadline = time.monotonic() - 1
        QTest.mouseClick(p.firefly, Qt.LeftButton, pos=p.firefly.rect().center())
        self.assertFalse(p.firefly.active)
        self.assertEqual(p.firefly.caught, 0)
        self.assertEqual(p.companion.data['xp'], 0)
        for stop in (lambda: p.start_focus(15), p.start_yarn, p.stop_play, p.toggle_nap,
                     p.follow_pointer, lambda: p.toggle('paused')):
            p.start_fireflies()
            self.assertTrue(p.firefly.active)
            stop()
            self.assertFalse(p.firefly.isVisible())

    def test_card_fits_below_pet_at_top_of_screen_and_has_opaque_body(self):
        p = self.pet
        screen = p.screen().availableGeometry()
        p.move(screen.center().x(), screen.top())
        p.card.open_card()
        self.app.processEvents()
        self.assertTrue(screen.contains(p.card.geometry()))
        self.assertGreater(p.card.y(), p.geometry().bottom())
        img = p.card.grab().toImage()
        self.assertEqual(img.pixelColor(7, 100).alpha(), 255)
        self.assertEqual(img.pixelColor(0, 0).alpha(), 0)

    def test_animation_reuses_one_window_shape_and_prepared_frames(self):
        p = self.pet
        shape = p.mask()
        frame_count = len(p.sprites.frames)
        clock = [1000.]
        p.mode, p.mode_started, p.mode_until, p.last_tick = 'running-right', 1000., 1010., 1000.
        with patch('time.monotonic', side_effect=lambda: clock[0]), \
                patch.object(p, 'setMask', wraps=p.setMask) as shapes:
            for _ in range(200):
                clock[0] += .04
                p.tick()
        self.assertEqual(shapes.call_count, 0)
        self.assertEqual(p.mask(), shape)
        self.assertEqual(len(p.sprites.frames), frame_count)
        for frame_shape in p.sprites.masks.values():
            self.assertTrue(frame_shape.subtracted(shape).isEmpty())
        self.assertFalse(shape.contains(QPoint(0, 0)))

    def test_resting_effects_only_show_once_and_redraw_when_changed(self):
        p = self.pet
        p.companion.data['sleeping'] = True
        clock = [1000.]
        p.last_tick = clock[0]
        with patch('time.monotonic', side_effect=lambda: clock[0]), \
                patch.object(p.effects, 'show', wraps=p.effects.show) as shows, \
                patch.object(p.effects, 'update', wraps=p.effects.update) as redraws:
            for _ in range(250):
                clock[0] += .04
                p.tick()
        self.assertEqual(shows.call_count, 1)
        self.assertLessEqual(redraws.call_count, 11)
        self.assertEqual(p.ticker.interval(), 200)

    def test_expired_bubble_has_no_opaque_trail(self):
        p = self.pet
        p.companion.data['sleeping'] = True
        p.effects.say('A short bubble')
        self.app.processEvents()
        sample = p.effects.bubble[0].topLeft() + QPoint(8, 8)
        before = p.effects.grab().toImage()
        self.assertGreater(before.pixelColor(sample - p.effects.pos()).alpha(), 200)
        p.effects.message_until = 0
        p.effects.tick(.04)
        self.app.processEvents()
        after = p.effects.grab().toImage()
        current_position = sample - p.effects.pos()
        self.assertIsNone(p.effects.bubble)
        if after.rect().contains(current_position):
            self.assertEqual(after.pixelColor(current_position).alpha(), 0)

    def test_bubble_themes_and_long_text_wrap(self):
        themes = [theme_for(pet, 'original') for pet in ('cat', 'cat-classic', 'monkey', 'eagle')]
        self.assertEqual(len({theme[0] for theme in themes}), 4)
        self.assertEqual(len({theme[1] for theme in themes}), 4)
        self.assertNotEqual(theme_for('monkey', 'original'), theme_for('monkey', 'pastel'))
        self.assertNotEqual(theme_for('eagle', 'original'), theme_for('eagle', 'night'))
        text = fit_text('🦅 hello ' * 14 + 'averylongword' * 12, 154)
        self.assertEqual(len(text.lines), 3)
        self.assertLessEqual(text.width, 144)
        self.assertTrue(text.lines[-1].endswith('…'))

    def test_bubble_layout_fits_screen_corners_and_negative_monitor_coordinates(self):
        for screen in (QRect(0, 0, 1920, 1080), QRect(-800, -70, 800, 620), QRect(0, 0, 360, 270)):
            text = fit_text('I’ll hold on with my tail, too!', screen.width())
            for size in (96, 128, 160, 192):
                for x in (screen.left(), screen.right() - size + 1):
                    for edge, y in ((False, screen.top()), (True, screen.bottom() - size + 1)):
                        art = QRect(x, y, size, size)
                        box, above, tip = bubble_position(art, screen, text)
                        self.assertEqual(above, edge)
                        self.assertTrue(screen.contains(box))
                        self.assertFalse(art.intersects(box))
                        self.assertTrue(box.left() < tip < box.right())

    def test_bubble_repositions_and_switching_animals_clears_stale_dialogue(self):
        pet = self.pet
        screen = pet.screen().availableGeometry()
        pet.effects.say('An original message.')
        above = pet.effects.bubble[1]
        pet.move(screen.left() + 10, screen.top())
        pet.effects.tick(.02)
        self.assertTrue(above)
        self.assertFalse(pet.effects.bubble[1])
        self.assertTrue(screen.contains(pet.effects.geometry()))
        pet.select_pet('eagle')
        self.assertFalse(pet.effects.message)
        self.assertFalse(pet.effects.isVisible())

    def test_focus_completion_has_only_one_animation_pass(self):
        p = self.pet
        p.companion.data['focus_until'] = time.time() - 1
        p.last_model_tick = 0
        with patch.object(p, 'frame_at', wraps=p.frame_at) as frames:
            p.tick()
        self.assertEqual(frames.call_count, 1)
        self.assertEqual(p.companion.data['focus_sessions'], 1)

    def test_toy_gets_smooth_clock_and_idle_clock_backs_off(self):
        p = self.pet
        p.start_yarn()
        self.assertEqual(p.ticker.interval(), 16)
        p.stop_play()
        p.effects.message = ''
        p.effects.particles.clear()
        p.companion.data['sleeping'] = True
        p.tick()
        self.assertEqual(p.ticker.interval(), 200)


if __name__ == '__main__':
    unittest.main()
