"""The standalone window for Pixel Pet's appearance, play, and settings."""
from PySide6.QtCore import QElapsedTimer, QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap, QPolygon
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QProgressBar,
                               QScrollArea, QSizePolicy, QStackedWidget, QTabBar, QVBoxLayout, QWidget)

from bubbles import PAW, STAR
from controls_activity import OptionsPage, PlayPage
from controls_appearance import AppearancePage
from controls_vines import paint_vines
from habitat import bounded_position, top_left_bounds
from play import pixel_shape


CONTROLS_SIZE = QSize(560, 486)
SLIDERS = ('0000000', '0100000', '1111111', '0100010', '1111111', '0000010', '0000000')
HABITAT_COLOURS = {
    'cat': ('#24314b', '#687768', '#465d49', '#2a4935', '#d7e6b1'),
    'cat-classic': ('#53634d', '#929064', '#587249', '#34543a', '#f6d997'),
    'monkey': ('#233d34', '#617d4e', '#3d6241', '#284d34', '#e3d789'),
    'eagle': ('#374c5d', '#8b8971', '#656d61', '#3e5549', '#ffe2a7'),
    'owl': ('#27283e', '#5a646b', '#3e514a', '#293f36', '#e5dba9'),
    'hoots': ('#27283e', '#5a646b', '#3e514a', '#293f36', '#e5dba9'),
}
GARDEN_COLOURS = ('#2a3b3a', '#687d58', '#496650', '#2d5039', '#dddca2')
LEAF = ('0000001', '0000111', '0001101', '0011010', '0110100', '0111000', '1000000')

QUICK_MENU_STYLE = '''
QDialog#pixelPetQuickMenu { background: #202d20; border: 1px solid #667c45; }
QPushButton {
    color: #f2f2db; background: #293b27; border: 1px solid #445b39;
    border-radius: 5px; padding: 4px 10px; text-align: left; font-size: 13px;
}
QPushButton:hover, QPushButton:focus { color: #f0ffd7; background: #355631; border-color: #667c45; }
QPushButton:pressed { background: #2a4125; }
'''

CONTROLS_STYLE = '''
QDialog#pixelPetControls, QWidget#controlsViewport, QWidget#controlsPage { background: #151e17; }
QWidget { color: #f2f2db; font-size: 12px; }
QLabel { background: transparent; }
QLabel#petName { color: #f7f6dd; font-size: 25px; font-weight: 750; }
QLabel#petDetails { color: #c3d88a; font-weight: 650; }
QLabel#petMood, QLabel#muted { color: #bbc5a4; }
QLabel#sectionTitle { font-size: 14px; font-weight: 700; }
QLabel#optionLabel { color: #e0e6c6; font-weight: 650; }
QLabel#focusTimer { color: #c6dc87; font-weight: 700; }
QFrame#controlsHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #334831, stop:1 #233629);
    border: 1px solid #5a7349; border-radius: 12px;
}
QFrame#panel {
    background: #212f23; border: 1px solid #3c523b; border-radius: 10px;
}
QTabBar::tab {
    color: #d9dfbb; background: #253526; border: 1px solid #485c3b;
    border-radius: 7px; min-width: 65px; margin-right: 5px;
    padding: 6px 10px; font-weight: 650;
}
QTabBar::tab:last { margin-right: 0; }
QTabBar::tab:hover { color: #fffde6; background: #344b32; }
QTabBar::tab:selected { color: #f4ffd5; background: #395534; border-color: #b1cd75; }
QTabBar::tab:focus { border-color: #e0eaa3; }
QPushButton, QToolButton {
    color: #edf0d3; background: #2b3d2b; border: 1px solid #465d40;
    border-radius: 6px; padding: 5px 7px; font-weight: 600;
}
QPushButton:hover, QToolButton:hover { color: #ffffff; background: #3c5437; border-color: #7f965f; }
QPushButton:pressed, QToolButton:pressed { background: #202e22; }
QPushButton:checked, QToolButton:checked {
    color: #f0ffd7; background: #355631; border-color: #afc873;
}
QPushButton:focus, QToolButton:focus { border-color: #e3eca0; }
QPushButton:disabled, QToolButton:disabled { color: #969e87; background: #263025; border-color: #3a4835; }
QToolButton#petChoice {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #364c32, stop:1 #203125);
    padding: 3px 2px;
}
QToolButton#petChoice:hover { background: #3c5437; }
QToolButton#petChoice:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4d6839, stop:1 #2f4930);
    border-color: #b1cd75;
}
QToolButton#petChoice:focus { border-color: #e3eca0; }
QPushButton#colourChoice, QPushButton#sizeChoice, QPushButton#paceChoice { padding: 4px 6px; }
QPushButton[role="accent"] { color: #292719; background: #edcb88; border-color: #edcb88; }
QPushButton[role="accent"]:hover { background: #ffe8b4; border-color: #ffe8b4; }
QPushButton[role="accent"]:disabled { color: #969e87; background: #263025; border-color: #3a4835; }
QPushButton[role="quiet"] { color: #dce4c4; background: #253526; }
QPushButton[role="danger"] { color: #ffdfce; background: #3f2c25; border-color: #74523e; }
QPushButton[role="danger"]:hover { background: #593b2d; }
QCheckBox {
    color: #ebf0d2; spacing: 7px; padding: 4px;
    border: 1px solid transparent; border-radius: 6px;
}
QCheckBox:hover { background: #324631; }
QCheckBox:focus { border-color: #b1cd75; }
QCheckBox::indicator {
    width: 15px; height: 15px; margin-left: 1px;
    background: #182218; border: 1px solid #829469; border-radius: 5px;
}
QCheckBox::indicator:checked { background: #b8d47d; border-color: #b8d47d; }
QScrollArea { border: none; background: #151e17; }
QScrollBar:vertical { width: 9px; background: #202c20; margin: 1px 0; }
QScrollBar::handle:vertical { min-height: 30px; background: #5d7950; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #7b965f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
'''


def tab_icon(pattern):
    image = QPixmap(14, 14)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    pixel_shape(painter, pattern, 0, 0, QColor('#d4e69b'))
    painter.end()
    return QIcon(image)


class SpritePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.frame = QPixmap()
        self.crop = QRect()
        self.pet = ''
        self.setFixedSize(170, 64)
        self.setAccessibleName('Current pet preview')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        outline = QPainterPath()
        outline.addRoundedRect(bounds, 8, 8)
        painter.setClipPath(outline)
        sky, horizon, distance, foliage, sun = (
            QColor(colour) for colour in HABITAT_COLOURS.get(self.pet, GARDEN_COLOURS))
        background = QLinearGradient(0, 0, 0, self.height())
        background.setColorAt(0, sky)
        background.setColorAt(1, horizon)
        painter.fillPath(outline, background)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(Qt.NoPen)
        painter.setBrush(sun)
        painter.drawEllipse(QRect(125, 7, 17, 17))
        painter.setBrush(distance)
        if self.pet == 'eagle':
            peaks = ((0, 47), (32, 19), (48, 35), (71, 16), (105, 51), (144, 31), (170, 52))
        else:
            peaks = ((0, 42), (26, 27), (55, 39), (88, 31), (124, 44), (153, 28), (170, 40))
        painter.drawPolygon(QPolygon([QPoint(x, y) for x, y in (*peaks, (170, 64), (0, 64))]))
        painter.setBrush(foliage)
        painter.drawPolygon(QPolygon([QPoint(x, y) for x, y in (
            (0, 48), (28, 43), (51, 54), (107, 52), (139, 45), (170, 50), (170, 64), (0, 64))]))
        painter.setBrush(foliage.darker(130))
        for x, y in ((14, 33), (26, 38), (146, 36), (156, 30)):
            painter.fillRect(x - 1, y + 8, 3, 12, foliage.darker(130))
            painter.drawPolygon(QPolygon([QPoint(x, y), QPoint(x - 6, y + 12), QPoint(x + 6, y + 12)]))
            painter.drawPolygon(QPolygon([QPoint(x, y + 5), QPoint(x - 8, y + 17), QPoint(x + 8, y + 17)]))
        painter.fillRect(54, 57, 65, 1, horizon)
        if not self.frame.isNull():
            source = self.crop.intersected(self.frame.rect())
            if source.isEmpty():
                source = self.frame.rect()
            size = source.size().scaled(QSize(80, 55), Qt.KeepAspectRatio)
            position = QPoint((self.width() - size.width()) // 2, 57 - size.height())
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(QRect(position, size), self.frame, source)


class DismissibleDialog(QDialog):
    compact_vines = False

    def showEvent(self, event):
        # The pet can recreate its native surface when its stacking layer changes.
        self.winId()
        self.windowHandle().setTransientParent(self.owner.windowHandle())
        super().showEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        paint_vines(painter, self.rect(), compact=self.compact_vines)

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            QTimer.singleShot(0, self, self.dismiss_if_inactive)
        return super().event(event)

    def dismiss_if_inactive(self):
        if self.isVisible() and not self.isActiveWindow():
            self.hide()


class QuickMenu(DismissibleDialog):
    compact_vines = True

    def __init__(self, owner):
        # A managed dialog can lose focus normally, including to native Wayland windows.
        super().__init__(owner, Qt.Dialog | Qt.FramelessWindowHint)
        self.owner = owner
        self.anchor = QPoint()
        self.setObjectName('pixelPetQuickMenu')
        self.setWindowTitle('Pixel Pet Quick Menu')
        self.setStyleSheet(QUICK_MENU_STYLE)
        self.setFixedSize(158, 82)
        self.activation_check = QTimer(self)
        self.activation_check.setSingleShot(True)
        self.activation_check.timeout.connect(self.dismiss_if_inactive)

        self.leave_timer = QTimer(self)
        self.leave_timer.setSingleShot(True)
        self.leave_timer.setInterval(240)
        self.leave_timer.timeout.connect(self.dismiss_if_pointer_left)

        actions = QVBoxLayout(self)
        actions.setContentsMargins(15, 10, 15, 8)
        actions.setSpacing(2)
        self.hide_button = QPushButton('Hide')
        self.show_button = QPushButton('Show menu')
        self.hide_button.setIcon(tab_icon(LEAF))
        self.show_button.setIcon(tab_icon(PAW))
        self.hide_button.clicked.connect(owner.hide_pet)
        self.show_button.clicked.connect(lambda: owner.open_controls(self.anchor))
        for button in (self.hide_button, self.show_button):
            button.setCursor(Qt.PointingHandCursor)
            actions.addWidget(button, 1)

    def enterEvent(self, event):
        self.leave_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.leave_timer.start()
        super().leaveEvent(event)

    def dismiss_if_pointer_left(self):
        if not self.underMouse() and not self.owner.underMouse():
            self.hide()

    def open_at(self, point):
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.leave_timer.stop()
        self.activation_check.stop()
        self.anchor = point
        screen = QApplication.screenAt(point) or self.owner.screen() or QApplication.primaryScreen()
        area = screen.availableGeometry()
        pet = self.owner.mask().boundingRect().translated(self.owner.pos())
        x = pet.right() + 7
        if x + self.width() > area.right() + 1:
            x = pet.left() - self.width() - 6
        position = bounded_position(QPoint(x, point.y() - 10), top_left_bounds(self.rect(), area))
        self.move(position)
        self.show()
        self.show_button.setFocus()
        self.activateWindow()
        # Dismiss if the window manager declines activation.
        self.activation_check.start(500)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.focusNextPrevChild(event.key() == Qt.Key_Down)
        else:
            super().keyPressEvent(event)


class ControlsWindow(DismissibleDialog):
    def __init__(self, owner, pets):
        flags = Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        super().__init__(owner, flags)
        self.owner, self.pets = owner, pets
        self.setObjectName('pixelPetControls')
        self.setWindowTitle('Pixel Pet Zoo')
        self.setWindowIcon(owner.tray.icon())
        self.setStyleSheet(CONTROLS_STYLE)
        self.setFixedSize(CONTROLS_SIZE)
        self.positioned = False
        self.outside_time = QElapsedTimer()
        self.pointer_watch = QTimer(self)
        self.pointer_watch.setInterval(100)
        self.pointer_watch.timeout.connect(self.check_pointer)
        self.pointer_entered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 13, 17, 11)
        layout.setSpacing(8)
        hero = QFrame(objectName='controlsHero')
        head = QHBoxLayout(hero)
        head.setContentsMargins(12, 4, 7, 3)
        head.setSpacing(10)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        identity.addStretch()
        self.name = QLabel(objectName='petName', textFormat=Qt.PlainText, wordWrap=True)
        self.name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.details = QLabel(objectName='petDetails', textFormat=Qt.PlainText, wordWrap=True)
        self.mood = QLabel(objectName='petMood', wordWrap=True, textFormat=Qt.PlainText)
        for label in (self.name, self.details, self.mood):
            identity.addWidget(label)
        self.progress = QProgressBar()
        self.progress.setAccessibleName('Progress to next friendship level')
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.setStyleSheet('QProgressBar { background: #25352b; border: none; border-radius: 2px; }'
                                    'QProgressBar::chunk { background: #b5cd78; border-radius: 2px; }')
        identity.addWidget(self.progress)
        identity.addStretch()
        head.addLayout(identity, 1)
        self.preview = SpritePreview()
        head.addWidget(self.preview)
        layout.addWidget(hero)

        self.tabs = QTabBar(objectName='controlsTabs')
        self.tabs.setIconSize(QSize(14, 14))
        self.tabs.setDrawBase(False)
        pages = QStackedWidget()
        self.appearance = AppearancePage(owner, pets)
        self.play = PlayPage(owner)
        self.options = OptionsPage(owner)
        for name, pattern, page in (('Appearance', PAW, self.appearance), ('Play', STAR, self.play),
                                    ('Settings', SLIDERS, self.options)):
            self.tabs.addTab(tab_icon(pattern), name)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.viewport().setObjectName('controlsViewport')
            page.setObjectName('controlsPage')
            page.setAttribute(Qt.WA_StyledBackground)
            scroll.setWidget(page)
            pages.addWidget(scroll)
        self.tabs.currentChanged.connect(pages.setCurrentIndex)
        navigation = QHBoxLayout()
        navigation.addWidget(self.tabs, 1)
        close = QPushButton('Close', objectName='closeZoo')
        close.setAccessibleName('Close zoo menu')
        close.clicked.connect(self.hide)
        navigation.addWidget(close)
        layout.addLayout(navigation)
        layout.addWidget(pages, 1)
        for button in self.findChildren(QPushButton):
            button.setAutoDefault(False)
            button.setCursor(Qt.PointingHandCursor)

    def open_on(self, screen):
        area = screen.availableGeometry()
        available = area.size() - QSize(28, 52)
        self.setFixedSize(CONTROLS_SIZE.boundedTo(available.expandedTo(QSize(1, 1))))
        if self.windowState() & (Qt.WindowMinimized | Qt.WindowMaximized | Qt.WindowFullScreen):
            self.setWindowState(Qt.WindowNoState)
        if not self.positioned or not area.contains(self.frameGeometry()):
            self.move(area.center() - self.rect().center())
            self.positioned = True
        self.sync()
        self.pointer_entered = False
        self.outside_time.start()
        self.show()
        self.pointer_watch.start()
        self.raise_()
        self.activateWindow()

    def check_pointer(self):
        # Native decorations and other apps may receive the last leave event.
        if self.frameGeometry().contains(QCursor.pos()) or QApplication.mouseButtons():
            self.pointer_entered = True
            self.outside_time.restart()
        elif self.outside_time.elapsed() >= (450 if self.pointer_entered else 3000):
            self.hide()

    def hideEvent(self, event):
        self.pointer_watch.stop()
        super().hideEvent(event)

    def sync(self):
        self.appearance.sync()
        self.options.sync()
        self.preview.pet = self.owner.settings.data['pet']
        self.preview.crop = self.owner.mask().boundingRect()
        self.setWindowIcon(self.owner.tray.icon())
        self.set_frame(self.owner.current)
        self.sync_live()

    def sync_live(self):
        pet = self.owner.settings.data['pet']
        companion = self.owner.companion
        self.name.setText(companion.data['name'])
        level, earned, required = companion.friendship_progress
        self.details.setText(f'{self.pets[pet]}  ·  Level {level}  ·  {required - earned} XP to level {level + 1}')
        self.progress.setRange(0, required)
        self.progress.setValue(earned)
        self.mood.setText(companion.mood_for(pet))
        self.play.sync()

    def set_frame(self, frame):
        self.preview.frame = frame
        self.preview.update()
