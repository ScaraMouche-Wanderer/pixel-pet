"""Play and desktop controls for the Pixel Pet window."""
import shutil
import time

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import (QBoxLayout, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from animals import EXTRA_ANIMATIONS
from pet_moves import MOVES


STANDARD_ANIMATIONS = (
    ('waving', 'Wave'), ('jumping', 'Jump'), ('running', 'Work'),
    ('waiting', 'Think'), ('review', 'Happy'), ('failed', 'Oops'),
)


def _panel(parent, title, hint=None):
    frame = QFrame()
    frame.setObjectName('panel')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 9, 10, 10)
    layout.setSpacing(6)
    header = QHBoxLayout()
    header.setSpacing(8)
    heading = QLabel(title)
    heading.setObjectName('sectionTitle')
    header.addWidget(heading, 1)
    layout.addLayout(header)
    if hint:
        subtitle = QLabel(hint)
        subtitle.setObjectName('sectionHint')
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
    parent.addWidget(frame)
    return layout, header


def _grid(layout, columns):
    grid = QGridLayout()
    grid.setSpacing(6)
    for column in range(columns):
        grid.setColumnStretch(column, 1)
    layout.addLayout(grid)
    return grid


def _button(object_name, text, callback, role=None, tooltip=None):
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setMinimumHeight(28)
    button.setAutoDefault(False)
    button.setCursor(Qt.PointingHandCursor)
    if role:
        button.setProperty('role', role)
    if tooltip:
        button.setToolTip(tooltip)
    button.clicked.connect(callback)
    return button


def _move_badge(color):
    badge = QPixmap(10, 10)
    badge.fill(Qt.transparent)
    painter = QPainter(badge)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor('#172118'))
    painter.setBrush(QColor(color))
    painter.drawPolygon(QPolygonF([
        QPointF(5.0, 1.0), QPointF(9.0, 5.0), QPointF(5.0, 9.0), QPointF(1.0, 5.0),
    ]))
    painter.end()
    return QIcon(badge)


class PlayPage(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.move_buttons = []
        self.pose_buttons = []
        self.animation_animal = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.columns = QBoxLayout(QBoxLayout.TopToBottom)
        self.columns.setSpacing(8)
        self.companion_column, self.play_column = QVBoxLayout(), QVBoxLayout()
        for column in (self.companion_column, self.play_column):
            column.setSpacing(8)
            self.columns.addLayout(column, 1)
            self.columns.setAlignment(column, Qt.AlignTop)
        layout.addLayout(self.columns)

        care, _ = _panel(self.companion_column, 'Companion')
        care_grid = _grid(care, 2)
        care_grid.addWidget(
            _button('openPetCard', 'Open pet card', owner.open_control_card,
                    tooltip='View care meters, lifetime counts, and rename your companion'),
            0, 0)
        care_grid.addWidget(
            _button('cuddle', 'Pet / cuddle', lambda: self._run(owner.interact, 'cuddle'),
                    tooltip='Give a warm cuddle to boost affection and XP'),
            0, 1)
        self.treat = _button('treat', '', lambda: self._run(owner.interact, 'treat'),
                             tooltip='Offer a favourite snack to replenish fullness')
        care_grid.addWidget(self.treat, 1, 0)
        self.nap = _button('nap', '', lambda: self._run(owner.toggle_nap))
        care_grid.addWidget(self.nap, 1, 1)

        play, _ = _panel(self.play_column, 'Toys and tricks')
        play_grid = _grid(play, 2)
        self.trick = _button('trick', '', lambda: owner.launch_from_controls(owner.active_trick))
        play_grid.addWidget(self.trick, 0, 0)
        self.showtime = _button('showtime', '', lambda: owner.launch_from_controls(owner.start_showtime), 'accent')
        self.fireflies = _button('fireflies', 'Firefly hunt',
                                 lambda: owner.launch_from_controls(owner.start_fireflies),
                                 tooltip='Catch 5 glowing fireflies in 25 seconds (closes menu)')
        play_grid.addWidget(self.fireflies, 0, 1)
        play_grid.addWidget(self.showtime, 1, 0, 1, 2)
        self.follow = _button('follow', '', self._follow)
        self.follow.setCheckable(True)
        play_grid.addWidget(self.follow, 2, 0)
        play_grid.addWidget(
            _button('stopPlay', 'Stop current play', lambda: self._run(owner.stop_play), 'quiet',
                    tooltip='Stop active toys, outings, and roaming so your pet settles here'),
            2, 1)
        self.play_hint = QLabel()
        self.play_hint.setObjectName('sectionHint')
        self.play_hint.setWordWrap(True)
        play.addWidget(self.play_hint)

        focus, focus_header = _panel(self.play_column, 'Focus together',
                                     'Quiet study session (+20 XP when finished)')
        self.focus_timer = QLabel()
        self.focus_timer.setObjectName('focusTimer')
        self.focus_timer.setAccessibleName('Time remaining')
        focus_header.addWidget(self.focus_timer)
        durations = _grid(focus, 3)
        self.focus_buttons = []
        for index, minutes in enumerate((15, 25, 50)):
            button = _button(f'focus{minutes}', f'{minutes} min',
                             lambda checked=False, duration=minutes: self._run(owner.start_focus, duration),
                             tooltip=f'Start a {minutes}-minute quiet focus session')
            durations.addWidget(button, 0, index)
            self.focus_buttons.append(button)
        self.stop_focus = _button('stopFocus', 'Stop focus', lambda: self._run(owner.stop_focus), 'quiet',
                                  tooltip='End the current focus session early')
        focus.addWidget(self.stop_focus)

        animation, anim_header = _panel(self.companion_column, 'Animate')
        self.animate_status = QLabel()
        self.animate_status.setObjectName('sectionHint')
        anim_header.addWidget(self.animate_status)
        moves_label = QLabel('Signature moves · closes menu')
        moves_label.setObjectName('subSectionTitle')
        animation.addWidget(moves_label)
        self.animations = _grid(animation, 2)
        poses_label = QLabel('Poses · stays open')
        poses_label.setObjectName('subSectionTitle')
        animation.addWidget(poses_label)
        self.pose_grid = _grid(animation, 3)
        layout.addStretch()
        self.sync()

    def resizeEvent(self, event):
        minimum = (self.companion_column.minimumSize().width()
                   + self.play_column.minimumSize().width() + self.columns.spacing())
        direction = (QBoxLayout.LeftToRight if event.size().width() >= max(520, minimum)
                     else QBoxLayout.TopToBottom)
        if direction != self.columns.direction():
            self.columns.setDirection(direction)
        super().resizeEvent(event)

    def _run(self, callback, *args):
        callback(*args)
        self.sync()

    def _follow(self):
        if self.owner.follow_until > time.monotonic():
            self._run(self.owner.follow_pointer)
        else:
            self.owner.launch_from_controls(self.owner.follow_pointer)

    def _blocked_reason(self):
        owner = self.owner
        if owner.settings.data['paused']:
            return 'Animation is paused in Settings'
        if owner.companion.data['sleeping']:
            return 'Companion is napping — wake up first'
        if owner.companion.data['focus_until'] is not None:
            return 'Focus session active — stop focus or wait to play tricks'
        return None

    def sync(self):
        owner = self.owner
        companion = owner.companion
        sleeping = companion.data['sleeping']
        focusing = companion.data['focus_until'] is not None
        ready = owner.ready_for_trick()
        blocked_reason = self._blocked_reason()
        following = owner.follow_until > time.monotonic()

        self.treat.setText(owner.voice['treat_label'])
        self.nap.setText('Wake up' if sleeping else 'Take a nap')
        self.nap.setToolTip(
            'Wake your companion from its nap' if sleeping else 'Let your companion sleep and recharge energy'
        )
        self.trick.setText(owner.trick_label)
        self.trick.setEnabled(ready)
        self.trick.setToolTip(
            blocked_reason or f'Launch "{owner.trick_label}" on desktop (closes menu)'
        )
        self.showtime.setVisible(bool(owner.showtime_label))
        if owner.showtime_label:
            self.showtime.setText(f'Showtime · {owner.showtime_label}')
            self.showtime.setEnabled(ready)
            self.showtime.setToolTip(
                blocked_reason or f'Perform "{owner.showtime_label}" stunt routine (closes menu)'
            )
        self.follow.setText('Stop following' if following else 'Follow cursor (20s)')
        self.follow.setChecked(following)
        self.follow.setToolTip(
            'Stop following your cursor' if following else 'Follow your cursor horizontally for 20 seconds (closes menu)'
        )

        if blocked_reason:
            self.play_hint.setText(blocked_reason)
            self.play_hint.setVisible(True)
        elif owner.firefly.active:
            self.play_hint.setText('Firefly hunt in progress on desktop')
            self.play_hint.setVisible(True)
        elif owner.ball.active:
            self.play_hint.setText('Yarn ball active — grab and throw it on desktop')
            self.play_hint.setVisible(True)
        elif following:
            self.play_hint.setText('Following your cursor on desktop')
            self.play_hint.setVisible(True)
        else:
            self.play_hint.setVisible(False)

        self.focus_timer.setVisible(focusing)
        self.stop_focus.setVisible(focusing)
        if focusing:
            minutes, seconds = divmod(companion.remaining(), 60)
            self.focus_timer.setText(f'{minutes:02d}:{seconds:02d} left')

        pet = owner.settings.data['pet']
        if self.animation_animal != pet:
            self.animation_animal = pet
            for grid in (self.animations, self.pose_grid):
                while grid.count():
                    button = grid.takeAt(0).widget()
                    button.hide()
                    button.deleteLater()
            self.move_buttons.clear()
            self.pose_buttons.clear()
            for index, move in enumerate(MOVES[pet]):
                button = _button(
                    f'pet-move-{index}', move.name,
                    lambda checked=False, move=move: owner.launch_from_controls(lambda: owner.perform_pet_move(move)),
                )
                button.setIcon(_move_badge(move.color))
                button.setIconSize(QSize(10, 10))
                self.move_buttons.append(button)
                self.animations.addWidget(button, *divmod(index, 2))
            extra = EXTRA_ANIMATIONS.get(owner.animal, ())
            for index, (mode, text) in enumerate((*extra, *STANDARD_ANIMATIONS)):
                button = _button(
                    f'animate-{mode}', text,
                    lambda checked=False, pose=mode: owner.play(pose),
                    tooltip=f'Preview "{text}" pose on your pet',
                )
                self.pose_buttons.append(button)
                self.pose_grid.addWidget(button, *divmod(index, 3))

        self.animate_status.setText('Ready' if ready else 'Moves paused')
        for button in self.move_buttons:
            button.setEnabled(ready)
            button.setToolTip(
                blocked_reason or f'Run "{button.text()}" on desktop with particle props (closes menu)'
            )


class _OptionToggle(QCheckBox):
    def hitButton(self, position):
        return self.rect().contains(position)


class OptionsPage(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.toggles = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        movement, _ = _panel(
            layout, 'Movement and reactions',
            'Choose how your companion moves, reacts, and plays on its own.'
        )
        self._add_toggles(movement, (
            ('paused', 'Pause animation', 'Freeze animations and pause roaming without hiding your pet'),
            ('autonomous', 'Autonomous play', 'Allow idle tricks, signature moves, and spontaneous outings'),
            ('roam', 'Walk around', 'Let your companion wander across the usable area of its display'),
            ('motion_effects', 'Motion effects', 'Show dust, leaves, feathers, and trails while moving'),
            ('chatty', 'Little speech bubbles', 'Show idle chatter and launch greetings (direct reactions still reply)'),
        ))

        desktop, _ = _panel(
            layout, 'Desktop',
            'Control window stacking, startup behavior, and desktop shortcuts.'
        )
        self._add_toggles(desktop, (
            ('always_on_top', 'Always on top', 'Float your pet, bubbles, and toys above application windows'),
            ('autostart', 'Start at login', 'Launch Pixel Pet automatically when you sign in'),
        ))
        commands = _grid(desktop, 2)
        commands.addWidget(
            _button('bringHome', 'Bring pet home', owner.home,
                    tooltip='Move your pet back to its home corner on the primary display'),
            0, 0)
        if shutil.which('chatgpt'):
            commands.addWidget(
                _button('openChatGPT', 'Open ChatGPT / Codex', owner.open_chatgpt,
                        tooltip='Launch the desktop ChatGPT / Codex app'),
                0, 1)

        divider = QFrame()
        divider.setObjectName('divider')
        divider.setFrameShape(QFrame.HLine)
        desktop.addSpacing(2)
        desktop.addWidget(divider)
        quit_row = QHBoxLayout()
        quit_row.setSpacing(8)
        quit_note = QLabel('Preferences and friendship progress save automatically.')
        quit_note.setObjectName('sectionHint')
        quit_row.addWidget(quit_note, 1)
        quit_button = _button('quitPet', 'Quit', owner.quit, 'danger',
                              tooltip='Save progress and close Pixel Pet')
        quit_button.setMinimumWidth(96)
        quit_row.addWidget(quit_button)
        desktop.addLayout(quit_row)

        layout.addStretch()
        self.sync()

    def _add_toggles(self, layout, items):
        grid = _grid(layout, 2)
        for index, (key, text, tip) in enumerate(items):
            toggle = _OptionToggle(text)
            toggle.setObjectName(key)
            toggle.setToolTip(tip)
            toggle.setAccessibleName(text)
            toggle.setAccessibleDescription(tip)
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setMinimumHeight(30)
            toggle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            toggle.clicked.connect(lambda checked, name=key: self._apply(name, checked))
            self.toggles[key] = toggle
            grid.addWidget(toggle, index // 2, index % 2)

    def _apply(self, key, checked):
        if key == 'autostart':
            self.owner.set_autostart(checked)
        elif self.owner.settings.data[key] != checked:
            self.owner.toggle(key)
        self.sync()

    def sync(self):
        for key, toggle in self.toggles.items():
            checked = self.owner.autostart_path.exists() if key == 'autostart' else self.owner.settings.data[key]
            toggle.setChecked(checked)
