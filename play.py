"""Pixel effects, desktop toys, and the companion card."""
import math
import random
import time

from PySide6.QtCore import Qt, QEvent, QPoint, QRect
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRegion
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QProgressBar, QInputDialog)

from bubbles import bubble_position, fit_text, paint_bubble, theme_for


HEART = ['0110110', '1111111', '1111111', '0111110', '0011100', '0001000']
STAR = ['0001000', '0011100', '1111111', '0111110', '0011100', '0110110']
FISH = ['00111100', '01111110', '11110111', '01111110', '00111100']
BANANA = ['0000010', '0000110', '0000110', '1001110', '1111100', '0111000']
LEAF = ('00111', '01110', '11100', '10000')
FEATHER = ('00011', '00110', '01100', '11000', '10000')
DUST = ('010', '111', '010')
PARTICLES = {'heart': HEART, 'fish': FISH, 'banana': BANANA, 'star': STAR,
             'leaf': LEAF, 'feather': FEATHER, 'dust': DUST}
MOTION_MARKS = {'monkey': 'leaf', 'eagle': 'feather', 'owl': 'feather', 'hoots': 'feather'}
FIREFLY = ['000010000', '000111000', '101111101', '011111110', '001111100',
           '011010110', '100010001']
PET_SURFACE_FLAGS = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
LAYER_FLAGS = Qt.WindowStaysOnTopHint | Qt.WindowStaysOnBottomHint


def set_pet_layer(widget, always_on_top, desktop_surface=True):
    """Keep the widget off the taskbar and choose its stacking layer."""
    layer = Qt.WindowStaysOnTopHint if always_on_top else Qt.WindowStaysOnBottomHint
    flags = (widget.windowFlags() & ~LAYER_FLAGS) | layer
    visible, position = widget.isVisible(), widget.pos()
    if visible:
        widget.hide()
    # XWayland needs a fresh native window to switch between desktop and utility types.
    if widget.testAttribute(Qt.WA_WState_Created):
        widget.destroy(True, False)
    widget.setWindowFlags(flags)
    widget.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop, desktop_surface and not always_on_top)
    widget.move(position)
    if visible:
        widget.show()


def pixel_shape(painter, shape, x, y, color, scale=2):
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    for row, line in enumerate(shape):
        for column, bit in enumerate(line):
            if bit == '1':
                painter.drawRect(int(x + column * scale), int(y + row * scale), scale, scale)


class Effects(QWidget):
    def __init__(self, owner):
        super().__init__(None, PET_SURFACE_FLAGS | Qt.WindowTransparentForInput)
        self.owner = owner
        set_pet_layer(self, owner.settings.data['always_on_top'])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle('Pixel Pet Reactions')
        self.particles = []
        self.message = ''
        self.message_until = 0
        self.text_key = None
        self.bubble = None
        self.bubble_text = None
        self.theme_key = None
        self.art = QRect()
        self.last_phase = -1
        self.last_owner_geometry = None

    def ensure_visible(self):
        if self.owner.isVisible() and not self.isVisible():
            self.show()

    def hide(self):
        if self.isVisible():
            super().hide()
            # Recreate the native surface so XWayland reapplies its layer on the next show.
            self.destroy(True, False)

    def clear(self):
        self.message = ''
        self.particles.clear()
        self.bubble = None
        self.hide()

    def clear_motion(self):
        self.particles = [item for item in self.particles if 'duration' not in item]
        if self.isVisible():
            self.update()

    def leave_motion_marks(self, previous, delta, airborne=False, finale=False):
        if not self.owner.settings.data['motion_effects']:
            return
        pet, style = (self.owner.settings.data[key] for key in ('pet', 'style'))
        _, (_, outline, accent) = theme_for(pet, style)
        kind = MOTION_MARKS.get(pet, 'dust')
        x = previous.x() + self.owner.width() * .5
        y = previous.y() + self.owner.height() * (.53 if airborne else .82)
        for i in range(7 if finale else 2):
            lifetime = random.uniform(.24, .53)
            self.particles.append({
                'x': x + random.uniform(-8, 8), 'y': y + random.uniform(-5, 5),
                'vx': random.uniform(-30, 30) - delta.x() * 3,
                'vy': random.uniform(-35, 6) - delta.y(),
                'life': lifetime, 'duration': lifetime,
                'kind': 'star' if finale and i % 2 == 0 else kind,
                'color': accent if i % 2 == 0 else outline,
            })

    def say(self, message, seconds=3.2):
        self.message = message
        self.message_until = time.monotonic() + seconds
        self.anchor()
        self.ensure_visible()
        self.update()

    def burst(self, kind='heart', count=7):
        for i in range(count):
            self.particles.append({'x': random.uniform(-24, 24), 'y': 0.,
                                   'vx': random.uniform(-28, 28), 'vy': random.uniform(-65, -35),
                                   'life': random.uniform(1.1, 1.8), 'kind': kind,
                                   'color': random.choice(['#ff8eaf', '#fdb2cf']) if kind == 'heart'
                                   else '#ffda75' if kind == 'banana'
                                   else random.choice(['#c4afff', '#ffe1a0', '#93e6d5'])})
        self.anchor()
        self.ensure_visible()
        self.update()
        self.owner.wake_animation()

    def anchor(self):
        owner_geometry = self.owner.geometry()
        screen = (QApplication.screenAt(owner_geometry.center()) or self.owner.screen()
                  or QApplication.primaryScreen()).availableGeometry()
        self.art = self.owner.mask().boundingRect().translated(owner_geometry.topLeft())
        if self.art.isEmpty():
            self.art = owner_geometry
        origin = self.art.topLeft() + QPoint(self.art.width() // 2, 24)
        bounds = QRect(origin - QPoint(105, 124), origin + QPoint(105, 36))
        for item in self.particles:
            if 'duration' in item:
                bounds = bounds.united(QRect(round(item['x']), round(item['y']), 14, 14))
        self.bubble = None
        if self.message:
            key = self.message, screen.width()
            if key != self.text_key:
                self.text_key = key
                self.bubble_text = fit_text(self.message, screen.width())
            self.bubble = bubble_position(self.art, screen, self.bubble_text)
            bounds = bounds.united(self.bubble[0].adjusted(-2, -9, 5, 11))
        bounds = bounds.intersected(screen)
        if bounds.isEmpty():
            bounds = QRect(screen.left(), screen.top(), 1, 1)
        if self.geometry() == bounds:
            return False
        self.setGeometry(bounds)
        return True

    def tick(self, dt):
        now = time.monotonic()
        had_particles = bool(self.particles)
        for item in self.particles:
            item['life'] -= dt
            item['x'] += item['vx'] * dt
            item['y'] += item['vy'] * dt
            item['vy'] += 12 * dt
        self.particles = [item for item in self.particles if item['life'] > 0]
        expired = bool(self.message) and now >= self.message_until
        if expired:
            self.message = ''
        resting = self.owner.companion.data['sleeping'] or self.owner.companion.remaining() > 0
        phase = int(now) % 3 if resting and not self.owner.settings.data['paused'] else -1
        phase_changed = phase != self.last_phase
        self.last_phase = phase
        if self.particles or self.message or (resting and not self.owner.settings.data['paused']):
            moved = self.anchor()
            owner_geometry = self.owner.geometry()
            owner_moved = owner_geometry != self.last_owner_geometry
            self.last_owner_geometry = owner_geometry
            theme_key = self.owner.settings.data['pet'], self.owner.settings.data['style']
            theme_changed = theme_key != self.theme_key
            self.theme_key = theme_key
            was_hidden = not self.isVisible()
            self.ensure_visible()
            if had_particles or expired or phase_changed or moved or owner_moved or was_hidden or theme_changed:
                self.update()
        elif self.isVisible():
            self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setRenderHint(QPainter.Antialiasing, False)
        theme = theme_for(self.owner.settings.data['pet'], self.owner.settings.data['style'])
        origin = self.art.topLeft() + QPoint(self.art.width() // 2, 24) - self.pos()
        for item in self.particles:
            shape = PARTICLES[item['kind']]
            if 'duration' in item:
                color = QColor(item['color'])
                color.setAlpha(round(216 * item['life'] / item['duration']))
                pixel_shape(p, shape, item['x'] - self.x(), item['y'] - self.y(), color)
            else:
                pixel_shape(p, shape, origin.x() + item['x'], origin.y() + item['y'], item['color'])
        d = self.owner.companion.data
        if (d['sleeping'] or self.owner.companion.remaining() > 0) and not self.owner.settings.data['paused']:
            p.setFont(QFont('DejaVu Sans Mono', 10, QFont.Bold))
            p.setPen(QColor(theme[1][2]))
            p.drawText(origin.x() + 36, origin.y() - 10 - max(0, self.last_phase) * 5, 'z z')
        if self.message and self.bubble:
            box, above, tip = self.bubble
            paint_bubble(p, box.translated(-self.pos()), above, tip - self.x(), self.bubble_text, theme, pixel_shape)


class YarnBall(QWidget):
    def __init__(self, owner):
        super().__init__(None, PET_SURFACE_FLAGS)
        self.owner = owner
        set_pet_layer(self, owner.settings.data['always_on_top'])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(36, 36)
        self.setMask(QRegion(QRect(6, 6, 24, 24), QRegion.Ellipse))
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip('Grab and toss the yarn. Your pet will chase it!')
        self.active = False
        self.quiet = False
        self.arena = None
        self.dragging = False
        self.drag_offset = QPoint()
        self.xf = self.yf = 0.
        self.vx = self.vy = 0.
        self.started = 0.
        self.pointer = QPoint()
        self.pointer_time = 0.

    def launch(self, quiet=False, arena=None):
        self.arena = QRect(arena) if arena is not None else None
        g = self.play_area()
        offset = self.owner.geometry().center().x() - g.center().x()
        direction = random.choice((-1, 1)) if quiet and abs(offset) < g.width() * .16 else -1 if offset > 0 else 1
        self.xf = max(g.left(), min(self.owner.geometry().center().x() + direction * 45,
                                    g.right() - self.width()))
        self.yf = max(g.top(), min(self.owner.y() + 5, g.bottom() - self.height()))
        speed = random.uniform(115, 215) if quiet else 150.
        lift = random.uniform(105, 220) if quiet else 160.
        self.vx, self.vy = direction * speed, -lift
        self.started = time.monotonic()
        self.active, self.dragging = True, False
        self.quiet = quiet
        self.move(round(self.xf), round(self.yf))
        self.show()

    def stop(self):
        self.active, self.dragging = False, False
        self.hide()

    def play_area(self):
        return self.arena or (self.owner.screen() or QApplication.primaryScreen()).availableGeometry()

    def tick(self, dt):
        if not self.active or self.dragging:
            return
        if time.monotonic() - self.started > (11 if self.quiet else 35):
            self.stop()
            if not self.quiet:
                self.owner.effects.say('Same time tomorrow, yarn?')
            return
        g = self.play_area()
        self.vy += 490 * dt
        self.xf += self.vx * dt
        self.yf += self.vy * dt
        ground = g.bottom() - self.height() + 1
        if self.yf >= ground:
            self.yf = ground
            self.vy = -abs(self.vy) * .57 if abs(self.vy) > 28 else 0
            self.vx *= .94
        if self.xf <= g.left() or self.xf >= g.right() - self.width():
            self.xf = max(g.left(), min(self.xf, g.right() - self.width()))
            self.vx *= -.75
        if self.yf < g.top():
            self.yf = g.top()
            self.vy = abs(self.vy)
        position = QPoint(round(self.xf), round(self.yf))
        if position != self.pos():
            self.move(position)
        # Catch only when the toy is near a paw, never while the user holds it.
        paw = self.owner.mapToGlobal(QPoint(self.owner.width() // 2, round(self.owner.height() * .84)))
        if (time.monotonic() - self.started > .9 and
                abs(self.geometry().center().x() - paw.x()) < 35 and
                abs(self.geometry().center().y() - paw.y()) < 43):
            self.stop()
            self.owner.caught_yarn()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setPen(Qt.NoPen)
        for rect in [(12, 6, 12, 24), (8, 10, 20, 16), (6, 14, 24, 8)]:
            p.fillRect(*rect, QColor('#bda1ff'))
        for rect in [(10, 12, 16, 3), (9, 20, 16, 3), (17, 7, 3, 20)]:
            p.fillRect(*rect, QColor('#7e60ba'))
        p.fillRect(11, 10, 5, 3, QColor('#e1d3ff'))
        p.fillRect(27, 26, 6, 2, QColor('#bda1ff'))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.quiet = False
            self.dragging = True
            self.drag_offset = event.position().toPoint()
            self.pointer = event.globalPosition().toPoint()
            self.pointer_time = time.monotonic()
            self.vx = self.vy = 0
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.dragging:
            now = time.monotonic()
            point = event.globalPosition().toPoint()
            dt = max(.02, now - self.pointer_time)
            delta = point - self.pointer
            self.vx = max(-600., min(600., delta.x() / dt))
            self.vy = max(-600., min(600., delta.y() / dt))
            self.pointer, self.pointer_time = point, now
            position = point - self.drag_offset
            self.xf, self.yf = float(position.x()), float(position.y())
            self.move(position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            if time.monotonic() - self.pointer_time > .18:
                self.vx = self.vy = 0
            self.started = time.monotonic()
            self.setCursor(Qt.OpenHandCursor)


class Firefly(QWidget):
    """One small target at a time, confined to the pet's current screen."""
    target_count = 5
    duration = 25

    def __init__(self, owner):
        super().__init__(None, PET_SURFACE_FLAGS)
        self.owner = owner
        set_pet_layer(self, owner.settings.data['always_on_top'])
        self.active = False
        self.caught = 0
        self.deadline = 0.
        self.glowing = True
        self.setWindowTitle('Pixel Pet Firefly')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(38, 38)
        self.setMask(QRegion(QRect(3, 3, 32, 32), QRegion.Ellipse))
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('Click the firefly to catch it')

    def launch(self):
        self.caught = 0
        self.deadline = time.monotonic() + self.duration
        self.active = True
        self.place_target()
        self.show()

    def stop(self):
        self.active = False
        self.hide()

    def place_target(self):
        g = (self.owner.screen() or QApplication.primaryScreen()).availableGeometry()
        pet = self.owner.geometry()
        avoid = pet.adjusted(-12, -12, 12, 12)
        candidates = []
        for dx, dy in ((-210, -140), (210, -140), (-250, 0), (250, 0),
                       (-140, -240), (140, -240), (-140, 210), (140, 210)):
            x = min(max(pet.center().x() + dx, g.left()), g.right() - self.width() + 1)
            y = min(max(pet.center().y() + dy, g.top()), g.bottom() - self.height() + 1)
            candidate = QPoint(x, y)
            if (g.contains(QRect(candidate, self.size()))
                    and not QRect(candidate, self.size()).intersects(avoid)
                    and (candidate - self.pos()).manhattanLength() >= 55
                    and candidate not in candidates):
                candidates.append(candidate)
        if not candidates:
            corners = (g.topLeft(), g.topRight() - QPoint(self.width() - 1, 0),
                       g.bottomLeft() - QPoint(0, self.height() - 1),
                       g.bottomRight() - QPoint(self.width() - 1, self.height() - 1))
            candidates.extend(point for point in corners
                              if not QRect(point, self.size()).intersects(pet))
        self.move(random.choice(candidates) if candidates else self.pos())

    def tick(self, now):
        if not self.active:
            return
        if now >= self.deadline:
            self.stop()
            self.owner.effects.say(f'{self.caught}/{self.target_count} fireflies. They can wait until next time.')
            return
        glowing = int(now * 5) % 2 == 0
        if glowing != self.glowing:
            self.glowing = glowing
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor('#efd78c' if self.glowing else '#a89968'), 1))
        painter.setBrush(QColor('#262335'))
        painter.drawEllipse(QRect(5, 5, 28, 28))
        painter.setRenderHint(QPainter.Antialiasing, False)
        pixel_shape(painter, FIREFLY, 10, 11, '#ffe997' if self.glowing else '#e1be69')
        painter.fillRect(18, 19, 2, 4, QColor('#fff6d1'))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.active:
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if (event.button() != Qt.LeftButton or not self.active
                or not self.mask().contains(event.position().toPoint())):
            event.ignore()
            return
        event.accept()
        self.tick(time.monotonic())
        if not self.active:
            return
        self.caught += 1
        if self.caught == self.target_count:
            self.stop()
            self.owner.interact('fireflies')
        else:
            self.place_target()
            self.owner.play('waving')
            self.owner.effects.say(f'{self.caught}/{self.target_count} fireflies')


CARD_STYLE = '''
QWidget { color: #f4efff; font-family: "DejaVu Sans"; font-size: 12px; }
QLabel { border: none; background: transparent; }
QLabel#petAvatar { background: #242437; border: 1px solid #3b3651; border-radius: 10px; }
QLabel#petName { color: #fcf8ff; font-size: 19px; font-weight: bold; }
QLabel#muted { color: #c2b9d8; font-size: 11px; }
QLabel#level { color: #e8d6ff; font-size: 12px; font-weight: bold; }
QWidget#careMeters { background: #202132; border: 1px solid #303249; border-radius: 8px; }
QPushButton {
    background: #26273b; border: 1px solid #3d3d58; border-radius: 7px;
    padding: 6px 9px; text-align: center; font-weight: bold;
}
QPushButton#fireflies { background: #373047; border-color: #65577c; color: #ffe7a9; }
QPushButton#showtime { background: #393148; border-color: #725c89; color: #f7d9ff; }
QPushButton#focus { background: #32294b; border-color: #6b558c; color: #f0e0ff; }
QPushButton#quiet { background: transparent; border-color: transparent; color: #cbbde3; }
QPushButton:hover, QPushButton#focus:hover, QPushButton#fireflies:hover, QPushButton#quiet:hover,
QPushButton#showtime:hover {
    background: #443956; border-color: #8b74ae;
}
QPushButton:focus, QPushButton#focus:focus, QPushButton#fireflies:focus, QPushButton#quiet:focus,
QPushButton#showtime:focus {
    border-color: #e0c6ff;
}
QPushButton:pressed, QPushButton#focus:pressed, QPushButton#fireflies:pressed {
    background: #59496d;
}
QProgressBar { background: #35364e; border: none; border-radius: 3px; }
QProgressBar::chunk { background: #b79bf2; border-radius: 3px; }
QProgressBar#affection::chunk { background: #f29cba; }
QProgressBar#fullness::chunk { background: #f6d080; }
QProgressBar#energy::chunk { background: #92e2d1; }
QInputDialog { background: #202132; }
QLineEdit { color: #f2edff; background: #343044; border: 1px solid #c3a8ff; padding: 6px; }
'''


class PetCard(QWidget):
    def __init__(self, owner):
        super().__init__(owner, Qt.Tool | Qt.FramelessWindowHint)
        self.owner = owner
        self.renaming = False
        set_pet_layer(self, owner.settings.data['always_on_top'], desktop_surface=False)
        self.setWindowTitle('Pixel Pet Card')
        self.setObjectName('petCard')
        self.setStyleSheet(CARD_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAccessibleName('Pixel Pet card')
        self.setFixedWidth(328)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 13, 14, 12)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.avatar = QLabel(alignment=Qt.AlignCenter)
        self.avatar.setObjectName('petAvatar')
        self.avatar.setFixedSize(50, 50)
        self.avatar_pet = None
        header.addWidget(self.avatar)
        profile = QVBoxLayout()
        profile.setSpacing(1)
        self.name = QLabel(textFormat=Qt.PlainText, wordWrap=True)
        self.name.setObjectName('petName')
        profile.addWidget(self.name)
        self.mood = QLabel(wordWrap=True)
        self.mood.setObjectName('muted')
        profile.addWidget(self.mood)
        header.addLayout(profile, 1)
        close = QPushButton('×')
        close.setObjectName('quiet')
        close.setAccessibleName('Close pet card')
        close.setFixedSize(30, 30)
        close.clicked.connect(self.hide)
        header.addWidget(close, 0, Qt.AlignTop)
        outer.addLayout(header)

        friendship = QVBoxLayout()
        friendship.setSpacing(5)
        self.level = QLabel()
        self.level.setObjectName('level')
        friendship.addWidget(self.level)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setAccessibleName('Progress to next friendship level')
        friendship.addWidget(self.progress)
        outer.addLayout(friendship)

        care = QWidget()
        care.setObjectName('careMeters')
        care.setAttribute(Qt.WA_StyledBackground, True)
        meters = QHBoxLayout(care)
        meters.setSpacing(12)
        meters.setContentsMargins(10, 8, 10, 9)
        self.meters = {}
        for key, text in [('affection', 'Love'), ('fullness', 'Snacks'), ('energy', 'Energy')]:
            column = QVBoxLayout()
            column.setSpacing(4)
            title = QLabel()
            title.setObjectName('muted')
            column.addWidget(title)
            meter = QProgressBar()
            meter.setObjectName(key)
            meter.setTextVisible(False)
            meter.setRange(0, 100)
            meter.setFixedHeight(5)
            meter.setAccessibleName(text)
            column.addWidget(meter)
            self.meters[key] = (text, title, meter)
            meters.addLayout(column, 1)
        outer.addWidget(care)

        grid = QGridLayout()
        grid.setSpacing(7)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        actions = [
            ('Pet', lambda: owner.interact('pet')),
            ('Treat', lambda: owner.interact('treat')),
            ('Play', owner.active_trick),
            ('Firefly hunt', owner.start_fireflies),
            ('Take a nap', owner.toggle_nap),
            ('Follow me', owner.follow_pointer),
        ]
        for index, (text, callback) in enumerate(actions):
            button = QPushButton(text)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(34)
            button.clicked.connect(callback)
            grid.addWidget(button, index // 2, index % 2)
            if index == 3:
                button.setObjectName('fireflies')
                button.setToolTip('Catch five fireflies in 25 seconds to earn friendship XP.')
            if index == 4:
                self.nap_button = button
            if index == 1:
                self.treat_button = button
            if index == 2:
                self.trick_button = button
        outer.addLayout(grid)

        self.showtime_button = QPushButton()
        self.showtime_button.setObjectName('showtime')
        self.showtime_button.setCursor(Qt.PointingHandCursor)
        self.showtime_button.setMinimumHeight(32)
        self.showtime_button.clicked.connect(owner.start_showtime)
        outer.addWidget(self.showtime_button)

        self.focus_button = QPushButton()
        self.focus_button.setObjectName('focus')
        self.focus_button.setCursor(Qt.PointingHandCursor)
        self.focus_button.setMinimumHeight(34)
        self.focus_button.clicked.connect(self.focus_click)
        outer.addWidget(self.focus_button)

        footer = QHBoxLayout()
        footer.setSpacing(4)
        self.record = QLabel(wordWrap=True)
        self.record.setObjectName('muted')
        footer.addWidget(self.record, 1)
        rename = QPushButton('Rename')
        rename.setObjectName('quiet')
        rename.setToolTip('Give your companion a name')
        rename.clicked.connect(self.rename)
        footer.addWidget(rename, 0, Qt.AlignVCenter)
        outer.addLayout(footer)
        self.sync()

    def sync(self):
        companion = self.owner.companion
        d = companion.data
        pet = self.owner.settings.data['pet'], self.owner.settings.data['style']
        if self.avatar_pet != pet:
            self.avatar_pet = pet
            avatar = self.owner.sprites.frame(0, 0).scaled(42, 42, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.avatar.setPixmap(avatar)
        self.name.setText(d['name'])
        self.mood.setText(companion.mood_for(pet[0]))
        self.treat_button.setText(self.owner.voice['treat_label'])
        self.trick_button.setText(self.owner.trick_label)
        self.trick_button.setEnabled(self.owner.ready_for_trick())
        self.showtime_button.setVisible(bool(self.owner.showtime_label))
        self.showtime_button.setText(f'Showtime · {self.owner.showtime_label}')
        self.showtime_button.setEnabled(self.owner.ready_for_trick())
        level, earned, required = companion.friendship_progress
        self.level.setText(f'Friendship level {level}  ·  {required - earned} XP to level {level + 1}')
        self.progress.setToolTip(f"{d['xp']} total XP · {earned} / {required} XP this level")
        self.progress.setRange(0, required)
        self.progress.setValue(earned)
        for key, (text, title, meter) in self.meters.items():
            value = round(d[key])
            title.setText(f'{text} {value}%')
            meter.setValue(value)
        place = {'monkey': 'Edge climber', 'eagle': 'Glider', 'owl': 'Night flyer', 'hoots': 'Night flyer'}.get(
            pet[0], f"Yarn catches {d['catches']}")
        self.record.setText(f"Pets {d['pets']} · {place}\n"
                            f"Hunts won {d['firefly_rounds']} · Focus sessions {d['focus_sessions']}")
        self.nap_button.setText('Wake up' if d['sleeping'] else 'Take a nap')
        left = companion.remaining()
        if d['focus_until'] is not None:
            self.focus_button.setText(f'Stop focus · {left // 60:02d}:{left % 60:02d}')
        else:
            self.focus_button.setText('Focus together · 25 min')

    def focus_click(self):
        if self.owner.companion.data['focus_until'] is not None:
            self.owner.stop_focus()
        else:
            self.owner.start_focus(25)

    def rename(self):
        dialog = QInputDialog(self, Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        set_pet_layer(dialog, self.owner.settings.data['always_on_top'], desktop_surface=False)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setWindowTitle('Name your companion')
        dialog.setLabelText('Pet name:')
        dialog.setTextValue(self.owner.companion.data['name'])
        self.renaming = True
        try:
            accepted = dialog.exec()
            value = dialog.textValue()
        finally:
            self.renaming = False
            dialog.deleteLater()
        if accepted:
            self.owner.companion.rename(value)
            self.owner.save_profile()
            self.owner.sync_controls()
            self.sync()
            self.owner.effects.say(self.owner.voice['rename'])

    def open_card(self):
        self.sync()
        g = (self.owner.screen() or QApplication.primaryScreen()).availableGeometry()
        self.setFixedWidth(min(328, g.width() - 8))
        self.adjustSize()
        x = self.owner.geometry().center().x() - self.width() // 2
        above = self.owner.y() - self.height() - 8
        below = self.owner.geometry().bottom() + 9
        y = below if above < g.top() + 4 and below + self.height() <= g.bottom() - 3 else above
        self.move(max(g.left() + 4, min(x, g.right() - self.width() - 3)),
                  max(g.top() + 4, min(y, g.bottom() - self.height() - 3)))
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor('#655681'))
        painter.setBrush(QColor('#171825'))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 12, 12)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate and not self.renaming:
            self.hide()
        return super().event(event)
