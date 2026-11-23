#!/usr/bin/python
"""A tiny, configurable desktop companion."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPixmap, QRegion, QTransform, QImage
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon
from animals import (ACTIVITIES, ANIMAL_ROWS, BIRD_ROWS, FLYERS, MONKEY_ROWS,
                     PALETTES, PLAY_PACES, SHOWTIME, STYLES, TRICKS, Outing, animal_frame, owl_frame)
from pet_moves import MOVES, move_particles
from companion import Companion, voice_for
from controls import ControlsWindow, QuickMenu
from habitat import roaming_area
from play import Effects, Firefly, PetCard, YarnBall, PET_SURFACE_FLAGS, set_pet_layer

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
LOCAL_MASCOTS = {'hoots': 'Hoots (Owl)', 'codex': 'Codex', 'dewey': 'Dewey', 'fireball': 'Fireball',
                 'rocky': 'Rocky', 'seedy': 'Seedy', 'stacky': 'Stacky', 'bsod': 'BSOD',
                 'null-signal': 'Null Signal'}
LOCAL_SHEETS = {
    key: files[0] for key in LOCAL_MASCOTS
    if (files := sorted(ASSETS.glob(f'{key}-spritesheet-*.webp')))
}
PETS = {'cat': 'Cosmic Cat', 'cat-classic': 'Classic Cat', 'monkey': 'Monkey', 'eagle': 'Eagle',
        'owl': 'Dusk Owl', **{key: label for key, label in LOCAL_MASCOTS.items() if key in LOCAL_SHEETS}}
ROWS = {'idle': (0, [1680, 660, 660, 840, 840, 1920]),
        'running-right': (1, [120] * 7 + [220]),
        'running-left': (2, [120] * 7 + [220]),
        'waving': (3, [140] * 3 + [280]),
        'jumping': (4, [140] * 4 + [280]),
        'failed': (5, [140] * 7 + [240]),
        'waiting': (6, [150] * 5 + [260]),
        'running': (7, [120] * 5 + [220]),
        'review': (8, [150] * 5 + [280])}
CAT_ROWS = {'idle': (0, [2400, 500, 140, 2000]),
            'running-right': (1, [98, 130, 105, 155]), 'running-left': (4, [98, 130, 105, 155]),
            'crouch-right': (5, [190, 190]), 'crouch-left': (6, [190, 190]),
            'stretch': (7, [180, 270, 310, 210]), 'groom': (8, [160, 230, 210, 260]),
            'waving': (2, [180, 180, 240, 180]), 'jumping': (3, [160, 160, 220, 180]),
            'failed': (0, [200, 200, 350, 200]), 'waiting': (0, [900, 400, 200, 900]),
            'running': (1, [160] * 4), 'review': (2, [180, 180, 240, 180])}
DEFAULTS = {'pet': 'cat', 'size': 160, 'position': None, 'paused': False, 'roam': False,
            'chatty': True, 'always_on_top': False, 'autonomous': True, 'style': 'original',
            'motion_effects': True, 'play_pace': 'normal', 'appearance_revision': 2}
MENU_STYLE = '''
QMenu { background: #202127; color: #eeeef1; border: 1px solid #474952; border-radius: 8px; padding: 5px; font-size: 12px; }
QMenu::item { padding: 7px 24px; border-radius: 4px; }
QMenu::item:selected { background: #414451; }
QMenu::separator { height: 1px; background: #42434c; margin: 5px; }
'''


class Settings:
    def __init__(self, path=None):
        self.path = Path(path or Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'pixel-pet/settings.json')
        self.data = dict(DEFAULTS)
        self.data['pet_names'] = {}
        try:
            saved = json.loads(self.path.read_text())
            if isinstance(saved, dict):
                pet = saved.get('pet')
                if isinstance(pet, str):
                    if pet in PETS:
                        self.data['pet'] = pet
                    elif pet == 'hoots':
                        self.data['pet'] = 'owl'
                if saved.get('size') in (96, 128, 160, 192):
                    self.data['size'] = saved['size']
                if isinstance(saved.get('style'), str) and saved['style'] in STYLES:
                    self.data['style'] = saved['style']
                if isinstance(saved.get('play_pace'), str) and saved['play_pace'] in PLAY_PACES:
                    self.data['play_pace'] = saved['play_pace']
                for key in ('paused', 'roam', 'chatty', 'always_on_top', 'autonomous', 'motion_effects'):
                    if isinstance(saved.get(key), bool):
                        self.data[key] = saved[key]
                pos = saved.get('position')
                if isinstance(pos, list) and len(pos) == 2 and all(type(n) is int for n in pos):
                    self.data['position'] = pos
                if isinstance(saved.get('companion'), dict):
                    self.data['companion'] = saved['companion']
                if isinstance(saved.get('pet_names'), dict):
                    self.data['pet_names'] = {
                        key: value for key, value in saved['pet_names'].items()
                        if key in PETS and isinstance(value, str) and value.strip()
                    }
                # Apply the requested size increase once. Later size choices stay put.
                if saved.get('appearance_revision') != 2 and self.data['size'] == 128:
                    self.data['size'] = 160
        except (OSError, ValueError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.data, indent=2))
        tmp.chmod(0o600)
        tmp.replace(self.path)


class Sprites:
    def __init__(self, pet, width, style='original'):
        self.pet, self.style = pet, style
        self.is_cat = pet in ('cat', 'cat-classic')
        self.is_original_animal = pet in PALETTES
        self.has_look = not self.is_cat and not self.is_original_animal
        if self.is_cat:
            self.animations = CAT_ROWS
        elif pet == 'monkey':
            self.animations = {**ANIMAL_ROWS, **MONKEY_ROWS}
        elif pet in FLYERS:
            self.animations = {**(ANIMAL_ROWS if self.is_original_animal else ROWS), **BIRD_ROWS}
        else:
            self.animations = ROWS
        self.frames, self.masks = {}, {}
        if self.is_original_animal:
            self.width = self.height = width
            return
        if self.is_cat:
            sheet_path = ASSETS / ('cat-cosmic.png' if pet == 'cat' else 'cat.png')
        else:
            sheet_path = LOCAL_SHEETS[pet]
        self.sheet = QPixmap(str(sheet_path))
        if self.sheet.isNull():
            raise ValueError(f'Invalid pet sheet: {sheet_path}')
        if self.is_cat:
            if self.sheet.width() != self.sheet.height():
                raise ValueError(f'Invalid cat grid: {sheet_path}')
            self.cell_width = self.cell_height = self.sheet.width() / 4
            self.width = self.height = width
        elif self.sheet.size().width() != 1536 or self.sheet.size().height() != 2288:
            raise ValueError(f'Invalid pet sheet: {sheet_path}')
        else:
            self.cell_width, self.cell_height = 192, 208
            self.width, self.height = width, round(width * 208 / 192)

    def prepare(self):
        """Cache frames before playback and keep one stable native window shape."""
        keys = {(row, column) for row, durations in self.animations.values()
                for column in range(len(durations))}
        if self.has_look:
            keys.update((row, column) for row in (9, 10) for column in range(8))
        if self.is_original_animal:
            keys.add((0, 3))
        region = QRegion()
        for key in sorted(keys):
            self.frame(*key)
            region |= self.masks[key]
        return region

    def frame(self, row, column):
        key = row, column
        if key not in self.frames:
            raw = self.animal_or_sheet_frame(row, column)
            frame = raw.scaled(self.width, self.height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            if (self.is_cat or self.pet == 'hoots') and self.style != 'original':
                tint = QColor(250, 161, 222, 125) if self.style == 'pastel' else QColor(44, 123, 164, 126)
                painter = QPainter(frame)
                painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                painter.fillRect(frame.rect(), tint)
                painter.end()
            self.frames[key] = frame
            self.masks[key] = self.input_region(self.frames[key])
        return self.frames[key]

    def animal_or_sheet_frame(self, row, column):
        if self.is_original_animal:
            return animal_frame(self.pet, self.style, row, column)
        if self.pet == 'hoots' and row >= 12:
            base_column = (0, 1, 2, 0)[column] if row == 20 else 0
            base = self.sheet.copy(base_column * 192, 0, 192, 208)
            return owl_frame(base, row, column)
        crouching = self.is_cat and row in (5, 6)
        source_row = 1 if self.is_cat and row in (4, 5, 6) else row
        pose = column
        if self.is_cat and row in (7, 8):
            source_row, column = (0, (0, 1, 1, 0)[column]) if row == 7 else (2, (0, 1, 2, 1)[column])
        left, top = round(column * self.cell_width), round(source_row * self.cell_height)
        right, bottom = round((column + 1) * self.cell_width), round((source_row + 1) * self.cell_height)
        raw = self.sheet.copy(left, top, right - left, bottom - top)
        if self.is_cat and row in (4, 6):
            raw = raw.transformed(QTransform().scale(-1, 1))
        if crouching:
            frame = QPixmap(raw.size())
            frame.fill(Qt.transparent)
            height = round(raw.height() * (.77 if column == 0 else .68))
            painter = QPainter(frame)
            painter.drawPixmap(QRect(0, raw.height() - height, raw.width(), height), raw)
            painter.end()
            return frame
        if self.is_cat and row in (7, 8):
            frame = QPixmap(raw.size())
            frame.fill(Qt.transparent)
            painter = QPainter(frame)
            if row == 7:
                width = round(raw.width() * (1., 1.07, 1.12, 1.03)[pose])
                height = round(raw.height() * (.93, .73, .65, .89)[pose])
                painter.drawPixmap(QRect((raw.width() - width) // 2, raw.height() - height, width, height), raw)
            else:
                painter.translate(raw.width() * .5, raw.height() * .74)
                painter.rotate((0, -6, -10, -5)[pose])
                painter.translate(-raw.width() * .5, -raw.height() * .74)
                painter.drawPixmap(0, 0, raw)
            painter.end()
            return frame
        return raw

    @staticmethod
    def input_region(pixmap):
        # Generated art can contain almost invisible alpha specks. Only the
        # visible character should intercept clicks or enter the window shape.
        image = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
        pixels, stride = image.constBits(), image.bytesPerLine()
        region = QRegion()
        for y in range(image.height()):
            start = None
            offset = y * stride
            for x in range(image.width() + 1):
                visible = x < image.width() and pixels[offset + x * 4 + 3] >= 96
                if visible and start is None:
                    start = x
                elif not visible and start is not None:
                    region |= QRegion(QRect(start, y, x - start, 1))
                    start = None
        return region


class Pet(QWidget):
    def __init__(self, settings, preview=False):
        super().__init__(None, PET_SURFACE_FLAGS)
        self.settings, self.preview = settings, preview
        set_pet_layer(self, settings.data['always_on_top'])
        self.companion = Companion(settings.data.get('companion'))
        legacy_name = self.companion.data['name']
        self.companion.rename(settings.data['pet_names'].get(
            settings.data['pet'], self.voice['name'] if legacy_name == 'Mochi' else legacy_name))
        self.setWindowTitle('Pixel Pet')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setCursor(Qt.OpenHandCursor)
        self.setMouseTracking(True)
        self.setToolTip('Right-click: Hide or Show menu · Middle-click: pet card\n'
                        'Hold: cuddle · Double-click: jump · Drag: move · Stroke the head to purr')
        self.mode, self.mode_started, self.mode_until = 'waving', time.monotonic(), time.monotonic() + 2.1
        self.drag_origin = None
        self.dragged = False
        self.press_pos = QPoint()
        self.quick_menu = None
        self.frame_key = None
        self._frame_delay_ms = 100
        self._updating = False
        self.current = None
        self.direction = 1
        self.roam_offset = 0.0
        self.last_tick = time.monotonic()
        self.last_interaction = time.monotonic()
        self.next_outing = self.last_interaction + 1.8
        self.next_pet_move = self.last_interaction + random.uniform(8, 18)
        self.last_motion_mark = 0.
        self.activities = []
        self.last_activity = None
        self.outing = None
        self.last_saved = self.last_interaction
        self.last_model_tick = 0.
        self.last_chatter = self.last_interaction
        self.follow_until = 0.
        self.last_stroke = 0.
        self.stroke_distance = 0.
        self.hover_point = None
        self.intro_pending = not preview
        self.lock_handle = None
        self.load_pet()
        self.effects = Effects(self)
        self.ball = YarnBall(self)
        self.firefly = Firefly(self)
        self.card = PetCard(self)
        self.controls = None
        self.tray = QSystemTrayIcon(QIcon(self.sprites.frame(0, 0)), self)
        self.tray.setToolTip('Pixel Pet · click to show · right-click for controls')
        self.tray.activated.connect(self.tray_clicked)
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet(MENU_STYLE)
        self.tray_controls = self.tray_menu.addAction(
            'Show menu', lambda: QTimer.singleShot(0, self, self.open_controls))
        self.tray_visibility = self.tray_menu.addAction('Show pet', self.toggle_pet_visibility)
        self.tray_menu.addAction('Bring pet home', self.home)
        self.tray_menu.addAction('Quit', self.quit)
        self.update_tray_visibility()
        self.tray.setContextMenu(self.tray_menu)
        if not preview:
            self.tray.show()
        position = self.settings.data['position']
        if position:
            self.move(*position)
            self.clamp_position()
        else:
            self.home()
        self.recenter_roaming_area()
        self.ticker = QTimer(self)
        self.ticker.setTimerType(Qt.PreciseTimer)
        self.ticker.timeout.connect(self.tick)
        self.ticker.start(40)
        self.hold_timer = QTimer(self)
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self.cuddle_hold)
        self.tick()

    @property
    def autostart_path(self):
        return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'autostart/pixel-pet.desktop'

    @property
    def voice(self):
        return voice_for(self.settings.data['pet'])

    @property
    def trick_label(self):
        return TRICKS.get(self.settings.data['pet'], 'Toss yarn')

    @property
    def animal(self):
        pet = self.settings.data['pet']
        return 'cat' if pet == 'cat-classic' else pet

    @property
    def showtime_label(self):
        return SHOWTIME.get(self.animal)

    @property
    def play_pace(self):
        return PLAY_PACES[self.settings.data['play_pace']][1]

    def load_pet(self):
        self.sprites = Sprites(self.settings.data['pet'], self.settings.data['size'], self.settings.data['style'])
        region = self.sprites.prepare()
        self.current = self.sprites.frame(0, 0)
        self.setFixedSize(self.sprites.width, self.sprites.height)
        self.setMask(region)
        self.frame_key = None

    def select_pet(self, pet):
        self.stop_outing(return_to_perch=True)
        if self.ball.active and self.ball.quiet:
            self.ball.stop()
        if pet != self.settings.data['pet']:
            self.effects.clear()
        names = self.settings.data['pet_names']
        names[self.settings.data['pet']] = self.companion.data['name']
        self.settings.data['pet'] = pet
        self.companion.rename(names.get(pet, self.voice['name']))
        self.settings.data['companion'] = self.companion.snapshot()
        self.intro_pending = True
        self.activities = []
        self.last_activity = None
        self.next_outing = time.monotonic() + 1.8
        self.refresh_appearance()

    def select_style(self, style):
        self.settings.data['style'] = style
        self.stop_outing(return_to_perch=True)
        self.refresh_appearance()

    def refresh_appearance(self):
        self.settings.save()
        self.load_pet()
        self.clamp_position()
        self.recenter_roaming_area()
        icon = QIcon(self.sprites.frame(0, 0))
        self.tray.setIcon(icon)
        QApplication.instance().setWindowIcon(icon)
        self.play('waving')
        self.card.sync()
        self.sync_controls()

    def resize_pet(self, size):
        self.stop_outing(return_to_perch=True)
        bottom = self.geometry().bottom()
        self.settings.data['size'] = size
        self.load_pet()
        self.move(self.x(), bottom - self.height() + 1)
        self.clamp_position()
        self.recenter_roaming_area()
        self.remember_position()
        self.tick()
        self.sync_controls()

    def home(self):
        self.stop_outing()
        g = QApplication.primaryScreen().availableGeometry()
        self.move(g.right() - self.width() - 22, g.bottom() - self.height() - 12)
        self.recenter_roaming_area()
        self.show_pet()

    def clamp_position(self):
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        g = screen.availableGeometry()
        self.move(max(g.left(), min(self.x(), g.right() - self.width() + 1)),
                  max(g.top(), min(self.y(), g.bottom() - self.height() + 1)))

    def recenter_roaming_area(self):
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        self.roaming_area = roaming_area(self.geometry(), screen.availableGeometry())

    def adjust_to_screens(self):
        self.stop_toys()
        self.clamp_position()
        self.recenter_roaming_area()

    def remember_position(self):
        self.settings.data['position'] = [self.x(), self.y()]
        self.save_profile()

    def save_profile(self):
        self.settings.data['pet_names'][self.settings.data['pet']] = self.companion.data['name']
        self.settings.data['companion'] = self.companion.snapshot()
        self.settings.save()
        self.last_saved = time.monotonic()

    def wake_animation(self):
        # React immediately after an input event, even when the idle clock has
        # backed off. Tests and offscreen previews deliberately stop the clock.
        if hasattr(self, 'ticker') and self.ticker.isActive() and self.ticker.interval() != 16:
            self.ticker.setInterval(16)

    def interact(self, action):
        old_level = self.companion.level
        was_sleeping = self.companion.data['sleeping']
        self.companion.interact(action)
        self.companion.data['sleeping'] = False
        if action == 'pet':
            self.play('waving')
            self.effects.burst('heart', 5)
            message = self.voice['pet']
        elif action == 'treat':
            self.play('review')
            self.effects.burst(self.voice['treat_art'], 4)
            message = self.voice['treat']
        elif action == 'cuddle':
            self.play('review')
            self.effects.burst('heart', 12)
            message = self.voice['cuddle']
        elif action == 'catch':
            self.play('jumping')
            self.effects.burst('star', 12)
            message = f"Yarn conquered! Catch #{self.companion.data['catches']}"
        elif action == 'fireflies':
            self.play('jumping')
            self.effects.burst('star', 16)
            message = 'All five fireflies caught! +12 XP'
        leveled_up = self.companion.level > old_level
        if leveled_up:
            message += f' · Friendship level {self.companion.level}'
            if action != 'fireflies':
                self.effects.burst('star', 12)
        self.effects.say(message, 5 if leveled_up or action == 'fireflies' else 3.2)
        self.save_profile()
        self.card.sync()
        if was_sleeping or self.companion.level != old_level:
            self.sync_controls()

    def cuddle_hold(self):
        if self.drag_origin is not None and not self.dragged:
            self.interact('cuddle')

    def start_yarn(self):
        self.card.hide()
        self.stop_outing(return_to_perch=True)
        self.companion.data['sleeping'] = False
        self.companion.data['focus_until'] = None
        self.settings.data['paused'] = False
        self.follow_until = 0
        self.firefly.stop()
        self.ball.launch(arena=self.roaming_area if self.sprites.is_cat else None)
        self.effects.say('Toss it! You can grab the yarn.')
        self.last_interaction = time.monotonic()
        self.save_profile()
        self.sync_controls()
        self.tick()

    def caught_yarn(self):
        self.next_outing = time.monotonic() + random.uniform(1.3, 4.6)
        if self.ball.quiet:
            self.play('jumping')
            self.effects.burst('star', 5)
        else:
            self.interact('catch')

    def ready_for_trick(self):
        return (not self.settings.data['paused'] and not self.companion.data['sleeping']
                and self.companion.data['focus_until'] is None)

    def active_trick(self):
        if self.settings.data['pet'] in TRICKS:
            self.perform_trick(time.monotonic())
        else:
            self.start_yarn()

    def next_activity(self, animal):
        if not self.activities:
            signature, *others = ACTIVITIES[animal]
            if self.last_activity is None:
                random.shuffle(others)
                self.activities = [signature, *others]
            else:
                self.activities = [signature, *others]
                random.shuffle(self.activities)
                if self.activities[0] == self.last_activity:
                    self.activities.append(self.activities.pop(0))
        self.last_activity = self.activities.pop(0)
        return self.last_activity

    def perform_pet_move(self, move):
        pet = self.settings.data['pet']
        if move not in MOVES[pet] or not self.ready_for_trick():
            return
        self.stop_toys()
        self.follow_until = 0
        now = time.monotonic()
        self.next_pet_move = now + random.uniform(12, 28) / self.play_pace
        self.next_outing = max(self.next_outing, now + 3)
        if self.settings.data['motion_effects']:
            art = self.mask().boundingRect().translated(self.pos())
            self.effects.particles.extend(move_particles(move, art))
        self.play(move.pose)

    def start_showtime(self):
        if self.showtime_label and self.ready_for_trick():
            now = time.monotonic()
            self.intro_pending = False
            self.last_chatter = now
            self.perform_trick(now, activity=self.animal + '-show')
            if self.settings.data['chatty']:
                self.effects.say(f'{self.showtime_label}!', 2.2)

    def perform_trick(self, now, automatic=False, activity=None):
        pet = self.settings.data['pet']
        if pet not in TRICKS or not self.ready_for_trick():
            return
        if activity is None:
            activity = self.next_activity(self.animal) if automatic else ACTIVITIES[self.animal][0]
        self.next_outing = now + random.uniform(1.4, 4.9) / self.play_pace
        if not self.roaming_area.contains(self.geometry()):
            self.recenter_roaming_area()
        if activity == 'yarn':
            if automatic:
                self.ball.launch(quiet=True, arena=self.roaming_area)
            else:
                self.start_yarn()
            return
        self.card.hide()
        self.stop_toys()
        self.follow_until = 0
        bounds = self.roaming_area
        if activity == 'climb' or activity.endswith('-flight'):
            screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
            bounds = screen.availableGeometry()
        self.outing = Outing(activity, self.geometry(), bounds, now, pace=self.play_pace)
        self.wake_animation()

    def stop_outing(self, return_to_perch=False):
        if self.outing is not None:
            if return_to_perch:
                self.move(self.outing.origin)
                self.clamp_position()
            self.outing = None
            self.mode_until = 0

    def advance_outing(self, now):
        point, mode = self.outing.sample(now)
        if point != self.pos():
            self.move(point)
        if mode is None:
            if self.outing.activity.endswith('-show'):
                self.effects.leave_motion_marks(point, QPoint(), finale=True)
            self.clamp_position()
            self.stop_outing()
            self.next_outing = now + random.uniform(1.1, 4.7) / self.play_pace
        else:
            if self.mode != mode or now >= self.mode_until:
                self.mode_started = now
            self.mode, self.mode_until = mode, now + .30

    def start_fireflies(self):
        self.card.hide()
        self.stop_toys()
        self.companion.data['sleeping'] = False
        self.companion.data['focus_until'] = None
        self.settings.data['paused'] = False
        self.follow_until = 0
        self.intro_pending = False
        self.last_interaction = self.last_chatter = time.monotonic()
        self.firefly.launch()
        self.effects.say(f'Catch {self.firefly.target_count} fireflies in {self.firefly.duration} seconds!')
        self.save_profile()
        self.sync_controls()
        self.tick()

    def stop_toys(self):
        self.stop_outing(return_to_perch=True)
        self.ball.stop()
        self.firefly.stop()
        self.effects.clear_motion()

    def toggle_nap(self):
        sleeping = not self.companion.data['sleeping']
        self.companion.data['sleeping'] = sleeping
        self.companion.data['focus_until'] = None
        self.follow_until = 0
        self.stop_toys()
        self.mode_until = 0
        self.effects.say(self.voice['nap' if sleeping else 'wake'])
        self.save_profile()
        self.tick()
        self.card.sync()
        self.sync_controls()

    def follow_pointer(self):
        self.card.hide()
        if self.follow_until > time.monotonic():
            self.follow_until = 0
            self.recenter_roaming_area()
            self.effects.say('I will guard this spot.')
        else:
            self.companion.data['sleeping'] = False
            self.companion.data['focus_until'] = None
            self.settings.data['paused'] = False
            self.stop_toys()
            self.follow_until = time.monotonic() + 20
            self.effects.say(f"{self.voice['follow']} · 20 sec")
            self.save_profile()
        self.sync_controls()
        self.tick()

    def start_focus(self, minutes=25):
        self.stop_toys()
        self.follow_until = 0
        self.companion.start_focus(minutes)
        self.effects.say(self.voice['focus'].format(minutes=minutes), 4)
        self.save_profile()
        self.card.sync()
        self.tick()
        self.sync_controls()

    def stop_focus(self):
        self.companion.data['focus_until'] = None
        self.effects.say('We can try again whenever you like.')
        self.save_profile()
        self.card.sync()
        self.tick()
        self.sync_controls()

    def walk_towards(self, center_x, top_y, dt, speed=112):
        dx = center_x - self.geometry().center().x()
        dy = top_y - self.y()
        if abs(dx) < 5 and abs(dy) < 5:
            return
        step = max(1, speed * dt * self.play_pace)
        self.move(self.x() + round(max(-step, min(step, dx))),
                  self.y() + round(max(-step, min(step, dy))))
        self.clamp_position()
        mode = 'running-right' if dx > 0 else 'running-left'
        if self.mode != mode or time.monotonic() > self.mode_until:
            self.mode_started = time.monotonic()
        self.mode, self.mode_until = mode, time.monotonic() + .15

    def stop_play(self):
        self.stop_toys()
        self.follow_until = 0
        self.recenter_roaming_area()
        self.settings.data['roam'] = False
        self.next_outing = time.monotonic() + 5
        self.mode_until = 0
        self.effects.say('Settling in right here.')
        self.save_profile()
        self.sync_controls()

    def play(self, mode):
        self.mode = mode
        self.mode_started = time.monotonic()
        # Use the installed app's exact frame timing and three repetitions.
        self.mode_until = self.mode_started + sum(self.sprites.animations[mode][1]) * 3 / 1000
        self.last_interaction = self.mode_started
        if not self.isVisible():
            self.show_pet()
        self.tick()

    def frame_at(self, now, cursor):
        self._frame_delay_ms = 200
        if self.settings.data['paused']:
            return 0, 0
        if self.drag_origin is not None:
            return (0, 1) if self.sprites.is_cat or self.sprites.is_original_animal else (6, 1)
        if self.companion.data['sleeping']:
            if self.sprites.is_original_animal:
                return 0, 3
            return (0, 2) if self.sprites.is_cat else (0, 1)
        if self.companion.remaining() > 0:
            if self.sprites.is_original_animal:
                return 0, 3
            if self.sprites.is_cat:
                return 0, 2
            if self.animal in ('owl', 'hoots'):
                return 0, 1
            mode, elapsed = 'running', now * 1000
        elif now < self.mode_until:
            mode, elapsed = self.mode, (now - self.mode_started) * 1000
            if self.outing is not None:
                elapsed *= self.play_pace
        else:
            mode, elapsed = 'idle', (now - self.mode_until) * 1000
            center = self.geometry().center()
            dx, dy = cursor.x() - center.x(), cursor.y() - center.y()
            distance = math.hypot(dx, dy)
            # All sixteen original look directions, with idle blinking between looks.
            if self.sprites.has_look and 20 < distance < 260 and int(elapsed / 1000) % 8 < 5:
                self._frame_delay_ms = 33
                direction = round(((math.degrees(math.atan2(dx, -dy)) + 360) % 360) / 22.5) % 16
                return 9 + direction // 8, direction % 8
        row, durations = self.sprites.animations[mode]
        progress = elapsed % sum(durations)
        for column, duration in enumerate(durations):
            if progress < duration:
                self._frame_delay_ms = max(1, math.ceil(duration - progress))
                return row, column
            progress -= duration
        return row, 0

    def tick(self):
        # A catch or focus completion may start another animation. Never run a
        # second physics/paint pass inside the pass that is already in progress.
        if self._updating:
            return
        self._updating = True
        try:
            self._tick()
        finally:
            self._updating = False

    def _tick(self):
        now = time.monotonic()
        dt = max(0., min(.1, now - self.last_tick))
        self.last_tick = now
        visible = self.isVisible() or self.preview
        if now - self.last_model_tick >= 1:
            self.last_model_tick = now
            for event in self.companion.tick():
                if event == 'focus-complete':
                    if visible:
                        self.play('review')
                        self.effects.burst('star', 18)
                        self.effects.say(f"{self.voice['finish']} · Focus complete · +20 XP", 7)
                    if not self.preview and shutil.which('notify-send'):
                        subprocess.Popen(['notify-send', '--app-name=Pixel Pet', '--icon=' + str(ROOT / 'icon.png'),
                                          'Focus complete', f"{self.companion.data['name']} says: time for a stretch!"],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.save_profile()
            if self.card.isVisible():
                self.card.sync()
            if self.controls is not None and self.controls.isVisible():
                self.controls.sync_live()
        if not visible:
            self.ticker.setInterval(1000)
            return
        can_move = (not self.settings.data['paused'] and not self.companion.data['sleeping'] and
                    self.companion.remaining() == 0 and self.drag_origin is None and not self.card.isVisible()
                    and (self.quick_menu is None or not self.quick_menu.isVisible())
                    and QApplication.activePopupWidget() is None)
        previous = self.pos()
        if 0 < self.follow_until <= now:
            self.follow_until = 0
            self.recenter_roaming_area()
        if self.outing is not None:
            if can_move:
                self.advance_outing(now)
            else:
                self.stop_outing(return_to_perch=True)
        elif self.firefly.active:
            self.firefly.tick(now)
        elif self.ball.active:
            if not self.settings.data['paused']:
                self.ball.tick(dt)
            if self.ball.active and can_move:
                g = self.ball.play_area()
                x = max(g.left() + self.width() // 2,
                        min(self.ball.geometry().center().x(), g.right() - self.width() // 2 + 1))
                self.walk_towards(x, g.bottom() - self.height() + 1, dt, 150)
        elif self.follow_until > now and can_move:
            pointer = QCursor.pos()
            g = (self.screen() or QApplication.primaryScreen()).availableGeometry()
            goal = max(g.left() + 50, min(pointer.x() - 55, g.right() - 50))
            self.walk_towards(goal, self.y(), dt)
        elif (self.settings.data['autonomous'] and can_move and now >= self.next_pet_move
              and now >= self.mode_until and not self.underMouse()
              and not (self.controls and self.controls.isVisible())):
            self.perform_pet_move(random.choice(MOVES[self.settings.data['pet']]))
        elif (self.settings.data['autonomous'] and self.settings.data['pet'] in TRICKS
              and can_move and now >= self.next_outing and now - self.last_interaction >= 1):
            self.perform_trick(now, automatic=True)
        elif (self.settings.data['roam'] and can_move
                and not self.underMouse() and now - self.last_interaction > 6):
            g = (self.roaming_area if self.settings.data['pet'] in TRICKS
                 else (self.screen() or QApplication.primaryScreen()).availableGeometry())
            self.roam_offset += 32 * dt
            if self.roam_offset >= 1:
                step = int(self.roam_offset)
                self.roam_offset -= step
                x = max(g.left(), min(self.x() + self.direction * step, g.right() - self.width() + 1))
                self.move(x, self.y())
            if self.x() <= g.left() + 2 or self.x() + self.width() >= g.right() - 2:
                self.direction *= -1
            self.mode = 'running-right' if self.direction > 0 else 'running-left'
            if now > self.mode_until:
                self.mode_started = now
            self.mode_until = now + .15
        displacement = self.pos() - previous
        if (can_move and self.mode_until > now and displacement.manhattanLength() > 0
                and self.settings.data['motion_effects'] and now - self.last_motion_mark >= .13):
            lift = self.mode.startswith(('trick-', 'stunt-', 'swing-')) or self.mode == 'jumping'
            self.effects.leave_motion_marks(previous, displacement, airborne=lift)
            self.last_motion_mark = now
        key = self.frame_at(now, QCursor.pos())
        if key != self.frame_key:
            self.frame_key = key
            self.current = self.sprites.frame(*key)
            self.update()
            if self.controls is not None and self.controls.isVisible():
                self.controls.set_frame(self.current)
        self.effects.tick(dt)
        if now - self.last_saved > 30:
            self.save_profile()
        if self.intro_pending and now - self.last_interaction > 1:
            self.intro_pending = False
            if self.settings.data['chatty']:
                self.effects.say(self.voice['hello'], 4)
        if (self.settings.data['chatty'] and not self.settings.data['paused'] and can_move and
                self.outing is None and not self.ball.active and not self.firefly.active and self.follow_until < now and
                now - self.last_chatter > 150):
            self.last_chatter = now
            self.effects.say(random.choice(self.voice['idle']))
        moving = can_move and (self.outing is not None or self.ball.active or self.follow_until > now or
                                (not self.firefly.active and self.settings.data['roam'] and
                                 now - self.last_interaction > 6))
        fast_effects = bool(self.effects.particles) or (self.ball.active and not self.settings.data['paused'])
        interval = 16 if moving or fast_effects or self.drag_origin is not None else min(200, self._frame_delay_ms)
        if self.ticker.interval() != interval:
            self.ticker.setInterval(interval)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        if self.current is not None:
            painter.drawPixmap(0, 0, self.current)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.quick_menu is not None and self.quick_menu.isVisible():
            self.quick_menu.leave_timer.stop()

    def mousePressEvent(self, event):
        if self.quick_menu is not None:
            self.quick_menu.hide()
        if event.button() == Qt.LeftButton:
            self.stop_outing()
            self.card.hide()
            self.drag_origin = event.globalPosition().toPoint()
            self.press_pos = self.pos()
            self.dragged = False
            self.hold_timer.start(700)
            self.setCursor(Qt.ClosedHandCursor)
            self.wake_animation()
        elif event.button() == Qt.MiddleButton:
            self.stop_outing(return_to_perch=True)
            self.card.open_card()

    def leaveEvent(self, event):
        if self.quick_menu is not None and self.quick_menu.isVisible():
            self.quick_menu.leave_timer.start()
        self.hover_point = None
        self.stroke_distance = 0
        super().leaveEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'effects'):
            self.effects.hide()
        if getattr(self, 'quick_menu', None) is not None:
            self.quick_menu.hide()

    def mouseMoveEvent(self, event):
        if self.drag_origin is not None:
            delta = event.globalPosition().toPoint() - self.drag_origin
            if delta.manhattanLength() > QApplication.startDragDistance():
                self.dragged = True
                self.hold_timer.stop()
            if self.dragged:
                self.move(self.press_pos + delta)
                self.effects.anchor()
        else:
            point = event.position().toPoint()
            if (self.hover_point is not None and point.y() < self.height() * .7 and
                    time.monotonic() - self.last_stroke > 3):
                distance = (point - self.hover_point).manhattanLength()
                if distance < 40:
                    self.stroke_distance += distance
                if self.stroke_distance > 100:
                    self.stroke_distance = 0
                    self.last_stroke = time.monotonic()
                    self.interact('cuddle')
            self.hover_point = point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.hold_timer.stop()
            if self.dragged:
                self.clamp_position()
                self.recenter_roaming_area()
                self.remember_position()
            self.drag_origin = None
            self.last_interaction = time.monotonic()
            self.setCursor(Qt.OpenHandCursor)
        elif event.button() == Qt.RightButton:
            self.stop_outing()
            self.card.hide()
            self.last_interaction = time.monotonic()
            self.open_pet_menu(event.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mouseDoubleClickEvent(event)
        self.hold_timer.stop()
        self.drag_origin = None
        self.dragged = True
        self.play('jumping')
        self.effects.burst('star', 8)
        self.effects.say(self.voice['jump'])

    def tray_clicked(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_pet()
            self.card.open_card()

    def show_pet(self):
        was_hidden = not self.isVisible()
        self.show()
        self.wake_animation()
        if was_hidden:
            self.update_tray_visibility()

    def hide_pet(self):
        self.stop_toys()
        self.follow_until = 0
        self.card.hide()
        if self.controls is not None:
            self.controls.hide()
        self.effects.clear()
        self.hide()
        self.update_tray_visibility()

    def open_pet_menu(self, point):
        if self.isVisible():
            if self.quick_menu is None:
                self.quick_menu = QuickMenu(self)
            self.quick_menu.open_at(point)

    def open_controls(self, point=None):
        if self.quick_menu is not None:
            self.quick_menu.hide()
        if self.controls is None:
            self.controls = ControlsWindow(self, PETS)
        self.card.hide()
        position = QCursor.pos() if point is None else point
        screen = QApplication.screenAt(position) or self.screen() or QApplication.primaryScreen()
        self.controls.open_on(screen)

    def open_control_card(self):
        self.launch_from_controls(self.card.open_card)

    def launch_from_controls(self, action):
        self.controls.hide()
        self.show_pet()
        action()

    def toggle_pet_visibility(self):
        if self.isVisible():
            self.hide_pet()
        else:
            self.show_pet()

    def update_tray_visibility(self):
        visible = self.isVisible()
        self.tray_controls.setVisible(visible)
        self.tray_visibility.setText('Hide' if visible else 'Show pet')

    def sync_controls(self):
        if self.controls is not None and self.controls.isVisible():
            self.controls.sync()

    def toggle(self, key):
        self.settings.data[key] = not self.settings.data[key]
        if key == 'autonomous':
            self.next_outing = time.monotonic() + 1.8
            if not self.settings.data[key]:
                self.stop_outing(return_to_perch=True)
                if self.ball.active and self.ball.quiet:
                    self.ball.stop()
        if key == 'always_on_top':
            for widget in (self, self.effects, self.ball, self.firefly):
                set_pet_layer(widget, self.settings.data[key])
            set_pet_layer(self.card, self.settings.data[key], desktop_surface=False)
        if key == 'paused' and self.settings.data['paused']:
            self.stop_outing(return_to_perch=True)
            self.effects.clear_motion()
            if self.ball.active and self.ball.quiet:
                self.ball.stop()
            if self.firefly.active:
                self.firefly.stop()
                self.effects.say('Fireflies tucked away.')
        if key == 'motion_effects' and not self.settings.data['motion_effects']:
            self.effects.clear_motion()
        self.settings.save()
        self.tick()
        self.sync_controls()

    def set_play_pace(self, pace):
        self.stop_outing(return_to_perch=True)
        self.effects.clear_motion()
        self.settings.data['play_pace'] = pace
        self.next_outing = time.monotonic() + 1.4
        self.settings.save()
        self.sync_controls()

    def set_autostart(self, checked):
        if checked:
            self.autostart_path.parent.mkdir(parents=True, exist_ok=True)
            command = ' '.join(desktop_argument(path) for path in (sys.executable, ROOT / 'pet.py'))
            self.autostart_path.write_text(
                '[Desktop Entry]\nType=Application\nName=Pixel Pet\n'
                f'Exec={command}\nIcon={ROOT / "icon.png"}\n'
                'Terminal=false\nCategories=Utility;\nStartupNotify=false\n'
            )
        else:
            self.autostart_path.unlink(missing_ok=True)
        self.sync_controls()

    def open_chatgpt(self):
        subprocess.Popen(['chatgpt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def quit(self):
        self.stop_toys()
        self.remember_position()
        self.effects.hide()
        self.card.hide()
        if self.quick_menu is not None:
            self.quick_menu.close()
        if self.controls is not None:
            self.controls.close()
        self.tray.hide()
        QApplication.instance().quit()

    def closeEvent(self, event):
        self.stop_toys()
        self.effects.hide()
        self.card.hide()
        if self.controls is not None:
            self.controls.close()
        self.ticker.stop()
        self.hold_timer.stop()
        super().closeEvent(event)


def desktop_argument(value):
    value = str(value).replace('%', '%%')
    escaped = ''.join('\\' + char if char in '\\"$`' else char for char in value)
    return '"' + escaped.replace('\\', '\\\\') + '"'


def main():
    parser = argparse.ArgumentParser(description='A small Codex-style desktop pet')
    parser.add_argument('--preview', type=Path, help='Render the original animations offscreen')
    args = parser.parse_args()
    if args.preview:
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    elif os.environ.get('DISPLAY'):
        os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
    app = QApplication(sys.argv[:1])
    app.setApplicationName('Pixel Pet')
    app.setDesktopFileName('pixel-pet')
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    settings = Settings(args.preview / 'isolated-settings.json' if args.preview else None)
    if not args.preview:
        lock_dir = settings.path.parent
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock = open(lock_dir / 'instance.lock', 'w')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # The running instance sees this request on its next timer tick.
            (lock_dir / 'show-request').touch()
            return
    pet = Pet(settings, preview=bool(args.preview))
    pet.show_pet()
    app.setWindowIcon(QIcon(pet.sprites.frame(0, 0)))
    if args.preview:
        args.preview.mkdir(parents=True, exist_ok=True)
        pet.ticker.stop()
        pet.sprites.frame(0, 0).save(str(args.preview / 'icon.png'))
        for key, (row, durations) in pet.sprites.animations.items():
            pet.sprites.frame(row, min(2, len(durations) - 1)).save(str(args.preview / (key + '.png')))
        # A contact sheet uses the original pixels, without repainting the art.
        canvas = QPixmap(4 * 192, math.ceil(len(PETS) / 4) * 238)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        for i, key in enumerate(PETS):
            sprites = Sprites(key, 192)
            painter.drawPixmap(i % 4 * 192, i // 4 * 238, sprites.frame(0, 0))
        painter.end()
        canvas.save(str(args.preview / 'pets.png'))
        pet.card.open_card()
        app.processEvents()
        pet.card.grab().save(str(args.preview / 'pet-card.png'))
        pet.card.hide()
        pet.start_fireflies()
        app.processEvents()
        pet.firefly.grab().save(str(args.preview / 'firefly.png'))
        pet.firefly.stop()
        pet.effects.say('Tiny paws. Big personality.')
        pet.effects.burst('heart', 8)
        pet.effects.tick(.3)
        app.processEvents()
        pet.effects.grab().save(str(args.preview / 'reactions.png'))
        print('Preview:', args.preview)
        pet.close()
        return
    request = settings.path.parent / 'show-request'
    request.unlink(missing_ok=True)
    def watch_request():
        if request.exists():
            request.unlink(missing_ok=True)
            pet.home()
            pet.play('waving')
    request_timer = QTimer()
    request_timer.timeout.connect(watch_request)
    request_timer.start(750)
    signal.signal(signal.SIGINT, lambda *_: pet.quit())
    signal.signal(signal.SIGTERM, lambda *_: pet.quit())
    for screen in app.screens():
        screen.availableGeometryChanged.connect(lambda *_: pet.adjust_to_screens())
    app.screenAdded.connect(
        lambda screen: screen.availableGeometryChanged.connect(lambda *_: pet.adjust_to_screens()))
    app.screenRemoved.connect(lambda *_: pet.adjust_to_screens())
    app.aboutToQuit.connect(pet.remember_position)
    app.aboutToQuit.connect(pet.save_profile)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
