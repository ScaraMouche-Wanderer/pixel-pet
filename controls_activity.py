"""Play and desktop controls for the Pixel Pet window."""
import shutil
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QBoxLayout, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from animals import EXTRA_ANIMATIONS
from pet_moves import MOVES


STANDARD_ANIMATIONS = (
    ('waving', 'Wave'), ('jumping', 'Jump'), ('running', 'Work'),
    ('waiting', 'Think'), ('review', 'Happy'), ('failed', 'Oops'),
)


def _panel(parent, title):
    frame = QFrame()
    frame.setObjectName('panel')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(9, 8, 9, 9)
    layout.setSpacing(6)
    header = QHBoxLayout()
    heading = QLabel(title)
    heading.setObjectName('sectionTitle')
    header.addWidget(heading, 1)
    layout.addLayout(header)
    parent.addWidget(frame)
    return layout, header


def _grid(layout, columns):
    grid = QGridLayout()
    grid.setSpacing(5)
    for column in range(columns):
        grid.setColumnStretch(column, 1)
    layout.addLayout(grid)
    return grid


def _button(object_name, text, callback, role=None):
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setMinimumHeight(30)
    button.setAutoDefault(False)
    button.setCursor(Qt.PointingHandCursor)
    if role:
        button.setProperty('role', role)
    button.clicked.connect(callback)
    return button


class PlayPage(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.move_buttons = []
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
        care_grid.addWidget(_button('openPetCard', 'Open pet card', owner.open_control_card), 0, 0)
        care_grid.addWidget(_button('cuddle', 'Pet / cuddle', lambda: self._run(owner.interact, 'cuddle')), 0, 1)
        self.treat = _button('treat', '', lambda: self._run(owner.interact, 'treat'))
        care_grid.addWidget(self.treat, 1, 0)
        self.nap = _button('nap', '', lambda: self._run(owner.toggle_nap))
        care_grid.addWidget(self.nap, 1, 1)

        play, _ = _panel(self.play_column, 'Toys and tricks')
        play_grid = _grid(play, 2)
        self.trick = _button('trick', '', lambda: owner.launch_from_controls(owner.active_trick))
        play_grid.addWidget(self.trick, 0, 0)
        self.showtime = _button('showtime', '', lambda: owner.launch_from_controls(owner.start_showtime), 'accent')
        play_grid.addWidget(_button('fireflies', 'Firefly hunt',
                                    lambda: owner.launch_from_controls(owner.start_fireflies)), 0, 1)
        play_grid.addWidget(self.showtime, 1, 0, 1, 2)
        self.follow = _button('follow', '', self._follow)
        play_grid.addWidget(self.follow, 2, 0)
        play_grid.addWidget(_button('stopPlay', 'Stop current play', lambda: self._run(owner.stop_play), 'quiet'),
                            2, 1)

        focus, focus_header = _panel(self.play_column, 'Focus together')
        self.focus_timer = QLabel()
        self.focus_timer.setObjectName('focusTimer')
        self.focus_timer.setAccessibleName('Time remaining')
        focus_header.addWidget(self.focus_timer)
        durations = _grid(focus, 3)
        for index, minutes in enumerate((15, 25, 50)):
            button = _button(f'focus{minutes}', f'{minutes} minutes',
                             lambda checked=False, duration=minutes: self._run(owner.start_focus, duration))
            durations.addWidget(button, 0, index)
        self.stop_focus = _button('stopFocus', 'Stop focus', lambda: self._run(owner.stop_focus), 'quiet')
        focus.addWidget(self.stop_focus)

        animation, _ = _panel(self.companion_column, 'Animate')
        self.animation_width = 2
        self.animations = _grid(animation, self.animation_width)
        layout.addStretch()
        self.sync()

    def resizeEvent(self, event):
        minimum = (self.companion_column.minimumSize().width()
                   + self.play_column.minimumSize().width() + self.columns.spacing())
        direction = (QBoxLayout.LeftToRight if event.size().width() >= max(500, minimum + 12)
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

    def sync(self):
        owner = self.owner
        companion = owner.companion
        self.treat.setText(owner.voice['treat_label'])
        self.nap.setText('Wake up' if companion.data['sleeping'] else 'Take a nap')
        self.trick.setText(owner.trick_label)
        self.trick.setEnabled(owner.ready_for_trick())
        self.showtime.setVisible(bool(owner.showtime_label))
        if owner.showtime_label:
            self.showtime.setText(f'Showtime · {owner.showtime_label}')
            self.showtime.setEnabled(owner.ready_for_trick())
        self.follow.setText('Stop following' if owner.follow_until > time.monotonic() else 'Follow my cursor (20s)')
        focusing = companion.data['focus_until'] is not None
        self.focus_timer.setVisible(focusing)
        self.stop_focus.setVisible(focusing)
        if focusing:
            minutes, seconds = divmod(companion.remaining(), 60)
            self.focus_timer.setText(f'{minutes:02d}:{seconds:02d}')
        pet = owner.settings.data['pet']
        if self.animation_animal != pet:
            self.animation_animal = pet
            while self.animations.count():
                button = self.animations.takeAt(0).widget()
                button.hide()
                button.deleteLater()
            self.move_buttons.clear()
            for index, move in enumerate(MOVES[pet]):
                button = _button(f'pet-move-{index}', move.name, lambda checked=False, move=move:
                                 owner.launch_from_controls(lambda: owner.perform_pet_move(move)))
                self.move_buttons.append(button)
                self.animations.addWidget(button, *divmod(index, self.animation_width))
            extra = EXTRA_ANIMATIONS.get(owner.animal, ())
            for index, (mode, text) in enumerate((*extra, *STANDARD_ANIMATIONS), start=len(MOVES[pet])):
                button = _button(f'animate-{mode}', text, lambda checked=False, pose=mode: owner.play(pose))
                row, column = divmod(index, self.animation_width)
                self.animations.addWidget(button, row, column)
        for button in self.move_buttons:
            button.setEnabled(owner.ready_for_trick())


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

        movement, _ = _panel(layout, 'Movement and reactions')
        self._add_toggles(movement, (
            ('paused', 'Pause animation'),
            ('autonomous', 'Autonomous play'),
            ('roam', 'Walk around'),
            ('motion_effects', 'Motion effects'),
            ('chatty', 'Little speech bubbles'),
        ))

        desktop, _ = _panel(layout, 'Desktop')
        self._add_toggles(desktop, (('always_on_top', 'Always on top'), ('autostart', 'Start at login')))
        commands = _grid(desktop, 2)
        commands.addWidget(_button('bringHome', 'Bring pet home', owner.home), 0, 0)
        if shutil.which('chatgpt'):
            commands.addWidget(_button('openChatGPT', 'Open ChatGPT / Codex', owner.open_chatgpt), 0, 1)
        desktop.addWidget(_button('quitPet', 'Quit', owner.quit, 'danger'))
        layout.addStretch()
        self.sync()

    def _add_toggles(self, layout, items):
        grid = _grid(layout, 2)
        for index, (key, text) in enumerate(items):
            toggle = _OptionToggle(text)
            toggle.setObjectName(key)
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setMinimumHeight(29)
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
