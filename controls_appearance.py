"""Sprite previews and appearance controls for the desktop companion."""
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget,
)

from animals import PALETTES, PLAY_PACES, STYLES, TRICKS
from bubbles import theme_for


SIZES = {96: 'Tiny', 128: 'Compact', 160: 'Default', 192: 'Large'}
SIZE_TIPS = {
    96: 'Tiny · 96 px sprite — subtle corner buddy',
    128: 'Compact · 128 px sprite',
    160: 'Default · 160 px sprite — recommended scale',
    192: 'Large · 192 px sprite — bold desktop presence',
}
PACE_TIPS = {
    'gentle': 'Gentle — slower, calmer movement and animation tempo',
    'normal': 'Normal — balanced everyday movement speed',
    'zoomies': 'Zoomies — faster, energetic roaming and tricks',
}
PORTRAIT_SIZE = QSize(46, 32)
HOOTS_SWATCHES = {
    'original': ('#895941', '#c68e54', '#fae9a5'),
    'pastel': ('#ba7b9d', '#db9cb0', '#fae1c3'),
    'night': ('#4b6375', '#6a809b', '#9bd7d9'),
}


def portrait_icon(sprites, size):
    idle = sprites.frame(0, 0)
    bounds = sprites.masks[0, 0].boundingRect()
    if not bounds.isEmpty():
        idle = idle.copy(bounds)
    sprite = idle.scaled(size, Qt.KeepAspectRatio, Qt.FastTransformation)
    portrait = QPixmap(size)
    portrait.fill(Qt.transparent)

    _, (_, _, accent) = theme_for(sprites.pet, sprites.style)
    center = QColor(accent)
    center.setAlpha(136)
    glow = QColor('#acc178')
    glow.setAlpha(72)
    edge = QColor('#1b2a20')
    edge.setAlpha(0)
    halo = QRadialGradient(QPointF(portrait.rect().center()), size.width() * .44)
    halo.setColorAt(0, center)
    halo.setColorAt(.65, glow)
    halo.setColorAt(1, edge)

    painter = QPainter(portrait)
    painter.fillRect(portrait.rect(), halo)
    painter.fillRect(5, size.height() - 4, size.width() - 10, 1, QColor(177, 185, 117, 105))
    painter.fillRect(9, size.height() - 8, 2, 6, QColor(177, 185, 117, 80))
    painter.fillRect(size.width() - 11, size.height() - 8, 2, 6, QColor(177, 185, 117, 80))
    painter.drawPixmap((portrait.width() - sprite.width()) // 2,
                       (portrait.height() - sprite.height()) // 2, sprite)
    painter.end()
    return QIcon(portrait)


def swatch_icon(pet, style):
    if pet in PALETTES:
        palette = PALETTES[pet][style]
        colors = (palette[2], palette[3], palette[5])
    elif pet == 'hoots':
        colors = HOOTS_SWATCHES[style]
    else:
        _, colors = theme_for(pet, style)
    swatch = QPixmap(22, 12)
    swatch.fill(Qt.transparent)
    painter = QPainter(swatch)
    painter.setRenderHint(QPainter.Antialiasing)
    for x, color in zip((0, 7, 14), colors):
        painter.setPen(QColor('#141e15'))
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(x + 0.5, 1.5, 6.0, 9.0), 1.5, 1.5)
    painter.end()
    return QIcon(swatch)


class AppearancePage(QWidget):
    def __init__(self, owner, pets):
        super().__init__()
        self.owner = owner
        self.pet_buttons = {}
        self.original_icons = {}
        self.preview_selection = None
        compact_roster = len(pets) <= 6
        self.portrait_size = QSize(62, 44) if compact_roster else PORTRAIT_SIZE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        roster_panel = QFrame(objectName='panel')
        roster_layout = QVBoxLayout(roster_panel)
        roster_layout.setContentsMargins(10, 8, 10, 9)
        roster_layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel('Choose an animal')
        title.setObjectName('sectionTitle')
        header.addWidget(title, 1)
        self.roster_hint = QLabel(f'{len(pets)} companions · switches immediately')
        self.roster_hint.setObjectName('sectionHint')
        header.addWidget(self.roster_hint)
        roster_layout.addLayout(header)

        roster = QGridLayout()
        roster.setSpacing(6)
        group = QButtonGroup(self)
        columns = 3 if compact_roster else 5
        last_row, remaining = divmod(len(pets), columns)
        for column in range(columns * 2):
            roster.setColumnStretch(column, 1)
        for index, (pet, name) in enumerate(pets.items()):
            icon = portrait_icon(type(owner.sprites)(pet, 96), self.portrait_size)
            button = QToolButton()
            button.setObjectName('petChoice')
            button.setText(name)
            button.setAccessibleName(f'Select {name}')
            button.setIcon(icon)
            button.setIconSize(self.portrait_size)
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            trick = TRICKS.get(pet)
            button.setToolTip(
                f'{name} — {trick} · Original, Pastel & Moonlight colours'
                if trick else f'{name} — Original colours · tracks pointer'
            )
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(84 if compact_roster else 60)
            button.clicked.connect(
                lambda checked=False, value=pet: self.choose('pet', value, owner.select_pet))
            group.addButton(button)
            row, column = divmod(index, columns)
            offset = columns - remaining if row == last_row else 0
            roster.addWidget(button, row, column * 2 + offset, 1, 2)
            self.pet_buttons[pet] = button
            self.original_icons[pet] = icon
        roster_layout.addLayout(roster)
        layout.addWidget(roster_panel)

        settings = QFrame(objectName='panel')
        selections = QVBoxLayout(settings)
        selections.setContentsMargins(10, 8, 10, 8)
        selections.setSpacing(5)

        style_header = QHBoxLayout()
        style_title = QLabel('Style & movement')
        style_title.setObjectName('sectionTitle')
        style_header.addWidget(style_title, 1)
        self.colour_hint = QLabel()
        self.colour_hint.setObjectName('sectionHint')
        style_header.addWidget(self.colour_hint)
        selections.addLayout(style_header)

        self.colour_label = QLabel('Colour')
        self.colour_buttons = self.add_choices(
            selections, self.colour_label, 'colourChoice', 'style', STYLES, owner.select_style)
        self.size_buttons = self.add_choices(
            selections, QLabel('Size'), 'sizeChoice', 'size', SIZES, owner.resize_pet)
        for size, button in self.size_buttons.items():
            button.setToolTip(SIZE_TIPS.get(size, f'{size} px'))
        self.pace_buttons = self.add_choices(
            selections, QLabel('Speed'), 'paceChoice', 'play_pace',
            {key: name for key, (name, _) in PLAY_PACES.items()}, owner.set_play_pace)
        for pace, button in self.pace_buttons.items():
            button.setToolTip(PACE_TIPS.get(pace, pace))
        layout.addWidget(settings)
        layout.addStretch()
        self.sync()

    def add_choices(self, layout, label, object_name, setting, choices, change):
        group = QButtonGroup(self)
        row = QHBoxLayout()
        row.setSpacing(6)
        label.setObjectName('optionLabel')
        label.setMinimumWidth(52)
        row.addWidget(label)
        buttons = {}
        for value, text in choices.items():
            button = QPushButton(text)
            button.setObjectName(object_name)
            button.setAccessibleName(f'{label.text()} {text}')
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(28)
            button.clicked.connect(
                lambda checked=False, choice=value: self.choose(setting, choice, change))
            group.addButton(button)
            row.addWidget(button, 1)
            buttons[value] = button
        layout.addLayout(row)
        return buttons

    def choose(self, setting, value, change):
        if self.owner.settings.data[setting] != value:
            change(value)
        self.sync()

    def sync(self):
        settings = self.owner.settings.data
        pet = settings['pet']
        allows_colour = pet in TRICKS
        style = settings['style'] if allows_colour else 'original'
        selection = pet, style
        if self.preview_selection != selection:
            if self.preview_selection is None or self.preview_selection[0] != pet:
                if self.preview_selection is not None:
                    old_pet = self.preview_selection[0]
                    self.pet_buttons[old_pet].setIcon(self.original_icons[old_pet])
                for value, button in self.colour_buttons.items():
                    button.setIcon(swatch_icon(pet, value) if allows_colour else QIcon())
                    button.setIconSize(QSize(22, 12))
                    button.setEnabled(allows_colour)
                    button.setToolTip(
                        f'Apply {STYLES[value]} palette'
                        if allows_colour else 'This companion keeps its original colours'
                    )
                self.colour_label.setToolTip(
                    'Switch between colour palettes' if allows_colour
                    else 'This companion uses its original colours.'
                )
                self.colour_hint.setText(
                    'All changes save automatically' if allows_colour
                    else 'Uses original colours only'
                )
            self.pet_buttons[pet].setIcon(portrait_icon(self.owner.sprites, self.portrait_size))
            self.preview_selection = selection
        self.pet_buttons[pet].setChecked(True)
        self.colour_buttons[style].setChecked(True)
        self.size_buttons[settings['size']].setChecked(True)
        self.pace_buttons[settings['play_pace']].setChecked(True)
