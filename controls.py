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


CONTROLS_SIZE = QSize(656, 580)
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
QDialog#pixelPetQuickMenu {
    background: #1f2c20; border: 1px solid #6b8449; border-radius: 9px;
}
QPushButton {
    color: #f2f2db; background: #293b27; border: 1px solid #48613d;
    border-radius: 6px; padding: 5px 11px; text-align: left; font-size: 13px; font-weight: 600;
}
QPushButton:hover { color: #f5ffd9; background: #375832; border-color: #7ea05b; }
QPushButton:focus { color: #f5ffd9; background: #355530; border: 1.5px solid #f0df8d; }
QPushButton:pressed { background: #233720; }
QToolTip {
    background: #172118; color: #f4f6dc; border: 1px solid #6b8552;
    border-radius: 6px; padding: 4px 7px; font-size: 11px;
}
'''

CONTROLS_STYLE = '''
QDialog#pixelPetControls, QWidget#controlsViewport, QWidget#controlsPage { background: #151e17; }
QWidget { color: #f2f2db; font-size: 12px; }
QLabel { background: transparent; }
QLabel#petName { color: #f8f7df; font-size: 23px; font-weight: 750; }
QLabel#petDetails { color: #c8de8f; font-weight: 650; }
QLabel#petMood { color: #cfd8ba; }
QLabel#careSummary { color: #9fb188; font-size: 11px; }
QLabel#muted, QLabel#sectionHint { color: #9eb08a; font-size: 11px; }
QLabel#sectionTitle { color: #f4f5db; font-size: 14px; font-weight: 700; }
QLabel#subSectionTitle { color: #bdd38b; font-size: 11px; font-weight: 700; }
QLabel#optionLabel { color: #e2e8c8; font-weight: 650; }
QLabel#focusTimer {
    color: #dff4a4; background: #2b4428; border: 1px solid #759956;
    border-radius: 9px; padding: 2px 8px; font-size: 11px; font-weight: 700;
}
QLabel#statusBadge {
    border-radius: 9px; padding: 2px 9px; font-size: 11px; font-weight: 700;
    color: #d9ebb2; background: #2b4129; border: 1px solid #59794c;
}
QLabel#statusBadge[state="paused"] {
    color: #ffe8b8; background: #413722; border-color: #8c7244;
}
QLabel#statusBadge[state="sleeping"] {
    color: #d7dfff; background: #29324b; border-color: #5d6e9e;
}
QLabel#statusBadge[state="focus"] {
    color: #e6ffb8; background: #2c4a2a; border-color: #82ad5b;
}
QLabel#statusBadge[state="play"] {
    color: #292719; background: #edcb88; border-color: #f3d9a1;
}
QFrame#controlsHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #344a32, stop:1 #223528);
    border: 1px solid #5c764b; border-radius: 12px;
}
QFrame#panel {
    background: #202e22; border: 1px solid #3c533b; border-radius: 10px;
}
QFrame#divider { background: #344834; max-height: 1px; min-height: 1px; border: none; }
QTabBar::tab {
    color: #d9dfbb; background: #253526; border: 1px solid #485c3b;
    border-radius: 7px; min-width: 72px; margin-right: 6px;
    padding: 6px 12px; font-weight: 650;
}
QTabBar::tab:last { margin-right: 0; }
QTabBar::tab:hover { color: #fffde6; background: #344b32; border-color: #749059; }
QTabBar::tab:selected { color: #f6ffd9; background: #3a5735; border-color: #b1cd75; }
QTabBar::tab:focus { border: 1.5px solid #f0df8d; }
QPushButton, QToolButton {
    color: #edf0d3; background: #2b3e2c; border: 1px solid #476041;
    border-radius: 6px; padding: 5px 8px; font-weight: 600;
}
QPushButton:hover, QToolButton:hover { color: #ffffff; background: #3c5638; border-color: #819b61; }
QPushButton:pressed, QToolButton:pressed { background: #202e22; }
QPushButton:checked, QToolButton:checked {
    color: #f4ffdc; background: #375933; border-color: #b4cf76;
}
QPushButton:focus, QToolButton:focus { border: 1.5px solid #f0df8d; }
QPushButton:disabled, QToolButton:disabled { color: #8c957f; background: #242e23; border-color: #364433; }
QToolButton#petChoice {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #354b31, stop:1 #1f3024);
    padding: 3px 3px 5px 3px; border-radius: 7px;
}
QToolButton#petChoice:hover { background: #3d5639; }
QToolButton#petChoice:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4e6a3a, stop:1 #2f4b30);
    border: 1.5px solid #b8d579;
}
QToolButton#petChoice:focus { border: 1.5px solid #f0df8d; }
QPushButton#colourChoice, QPushButton#sizeChoice, QPushButton#paceChoice { padding: 4px 7px; }
QPushButton[role="accent"] { color: #292719; background: #edcb88; border-color: #edcb88; font-weight: 700; }
QPushButton[role="accent"]:hover { background: #ffe5ad; border-color: #ffe5ad; }
QPushButton[role="accent"]:focus { border: 1.5px solid #fff7cf; }
QPushButton[role="accent"]:disabled { color: #8c957f; background: #242e23; border-color: #364433; }
QPushButton[role="quiet"] { color: #dce4c4; background: #243325; border-color: #41563c; }
QPushButton[role="quiet"]:hover { color: #f6fbdf; background: #314531; border-color: #6b8554; }
QPushButton[role="danger"] { color: #ffdfce; background: #3f2c25; border-color: #77533f; }
QPushButton[role="danger"]:hover { color: #fff1e8; background: #5a3b2e; border-color: #a67157; }
QPushButton[role="danger"]:focus { border: 1.5px solid #f0df8d; }
QCheckBox {
    color: #e6ecd0; spacing: 8px; padding: 5px 7px;
    border: 1px solid transparent; border-radius: 6px;
}
QCheckBox:hover { background: #2d402c; border-color: #466041; }
QCheckBox:checked { color: #f7ffe0; background: #273928; border-color: #4a6443; }
QCheckBox:focus { border: 1.5px solid #f0df8d; }
QCheckBox::indicator {
    width: 15px; height: 15px; margin-left: 1px;
    background: #172117; border: 1px solid #7d9165; border-radius: 5px;
}
QCheckBox::indicator:checked {
    background: #c7e289; border: 3px solid #263827;
}
QToolTip {
    background: #172118; color: #f4f6dc; border: 1px solid #6b8552;
    border-radius: 6px; padding: 4px 7px; font-size: 11px;
}
QScrollArea { border: none; background: #151e17; }
QScrollBar:vertical { width: 9px; background: #202c20; margin: 1px 0; border-radius: 4px; }
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
    def __init__(self, owner=None):
        super().__init__()
        self.owner = owner
        self.frame = QPixmap()
        self.crop = QRect()
        self.pet = ''
        self.setFixedSize(176, 70)
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName('Current pet preview')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.owner is not None and self.owner.ready_for_trick():
            self.owner.play('waving')
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        outline = QPainterPath()
        outline.addRoundedRect(bounds, 9, 9)
        painter.setClipPath(outline)
        sky, horizon, distance, foliage, sun = (
            QColor(colour) for colour in HABITAT_COLOURS.get(self.pet, GARDEN_COLOURS))
        background = QLinearGradient(0, 0, 0, self.height())
        background.setColorAt(0, sky)
        background.setColorAt(1, horizon)
        painter.fillPath(outline, background)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(Qt.NoPen)
        if self.pet in ('cat', 'owl', 'hoots'):
            star = QColor(sun)
            star.setAlpha(155)
            painter.setBrush(star)
            for sx, sy in ((22, 10), (49, 16), (82, 8), (105, 19)):
                painter.fillRect(sx, sy, 2, 2, star)
        painter.setBrush(sun)
        painter.drawEllipse(QRect(130, 8, 17, 17))
        painter.setBrush(distance)
        if self.pet == 'eagle':
            peaks = ((0, 51), (34, 21), (50, 38), (74, 17), (109, 55), (149, 34), (176, 56))
        else:
            peaks = ((0, 46), (27, 30), (57, 43), (91, 34), (129, 48), (158, 31), (176, 44))
        painter.drawPolygon(QPolygon([QPoint(x, y) for x, y in (*peaks, (176, 70), (0, 70))]))
        painter.setBrush(foliage)
        painter.drawPolygon(QPolygon([QPoint(x, y) for x, y in (
            (0, 53), (29, 47), (53, 59), (111, 57), (144, 49), (176, 55), (176, 70), (0, 70))]))
        painter.setBrush(foliage.darker(130))
        for x, y in ((15, 36), (27, 41), (151, 39), (162, 33)):
            painter.fillRect(x - 1, y + 8, 3, 13, foliage.darker(130))
            painter.drawPolygon(QPolygon([QPoint(x, y), QPoint(x - 6, y + 12), QPoint(x + 6, y + 12)]))
            painter.drawPolygon(QPolygon([QPoint(x, y + 5), QPoint(x - 8, y + 17), QPoint(x + 8, y + 17)]))
        painter.fillRect(54, 62, 68, 1, horizon)
        if not self.frame.isNull():
            source = self.crop.intersected(self.frame.rect())
            if source.isEmpty():
                source = self.frame.rect()
            size = source.size().scaled(QSize(84, 58), Qt.KeepAspectRatio)
            position = QPoint((self.width() - size.width()) // 2, 62 - size.height())
            shadow = QColor(14, 22, 16, 85)
            painter.setBrush(shadow)
            painter.drawEllipse(QRect(self.width() // 2 - max(12, size.width() // 3), 60,
                                      max(24, size.width() * 2 // 3), 5))
            painter.drawPixmap(QRect(position, size), self.frame, source)
        painter.setClipping(False)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor('#597349'))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(bounds, 9, 9)


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
        self.setFixedSize(172, 94)
        self.activation_check = QTimer(self)
        self.activation_check.setSingleShot(True)
        self.activation_check.timeout.connect(self.dismiss_if_inactive)

        self.leave_timer = QTimer(self)
        self.leave_timer.setSingleShot(True)
        self.leave_timer.setInterval(240)
        self.leave_timer.timeout.connect(self.dismiss_if_pointer_left)

        actions = QVBoxLayout(self)
        actions.setContentsMargins(16, 13, 16, 10)
        actions.setSpacing(5)
        self.hide_button = QPushButton('Hide')
        self.show_button = QPushButton('Show menu')
        self.hide_button.setIcon(tab_icon(LEAF))
        self.show_button.setIcon(tab_icon(PAW))
        self.hide_button.setToolTip('Hide your pet to the system tray')
        self.show_button.setToolTip('Open Appearance, Play, and Settings')
        self.hide_button.setAccessibleName('Hide pet to system tray')
        self.show_button.setAccessibleName('Show controls menu')
        self.hide_button.clicked.connect(owner.hide_pet)
        self.show_button.clicked.connect(lambda: owner.open_controls(self.anchor))
        for button in (self.hide_button, self.show_button):
            button.setAutoDefault(False)
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
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and isinstance(self.focusWidget(), QPushButton):
            self.focusWidget().click()
        else:
            super().keyPressEvent(event)


class ControlsWindow(DismissibleDialog):
    def __init__(self, owner, pets):
        flags = Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        super().__init__(owner, flags)
        self.owner, self.pets = owner, pets
        self._last_badge_state = None
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
        layout.setSpacing(9)
        hero = QFrame(objectName='controlsHero')
        head = QHBoxLayout(hero)
        head.setContentsMargins(14, 10, 11, 10)
        head.setSpacing(12)
        identity = QVBoxLayout()
        identity.setSpacing(2)
        identity.addStretch()

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.name = QLabel(objectName='petName', textFormat=Qt.PlainText, wordWrap=True)
        self.name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        title_row.addWidget(self.name, 1)
        self.status_badge = QLabel(objectName='statusBadge', textFormat=Qt.PlainText)
        self.status_badge.setAccessibleName('Current companion activity state')
        title_row.addWidget(self.status_badge, 0, Qt.AlignVCenter)
        identity.addLayout(title_row)

        self.details = QLabel(objectName='petDetails', textFormat=Qt.PlainText, wordWrap=True)
        self.mood = QLabel(objectName='petMood', wordWrap=True, textFormat=Qt.PlainText)
        self.care_summary = QLabel(objectName='careSummary', textFormat=Qt.PlainText)
        for label in (self.details, self.mood, self.care_summary):
            identity.addWidget(label)

        self.progress = QProgressBar()
        self.progress.setAccessibleName('Progress to next friendship level')
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(
            'QProgressBar { background: #1a271d; border: 1px solid #40583d; border-radius: 3px; }'
            'QProgressBar::chunk { background: #b8d379; border-radius: 2px; }'
        )
        identity.addSpacing(2)
        identity.addWidget(self.progress)
        identity.addStretch()
        head.addLayout(identity, 1)
        self.preview = SpritePreview(owner)
        head.addWidget(self.preview, 0, Qt.AlignVCenter)
        layout.addWidget(hero)

        self.tabs = QTabBar(objectName='controlsTabs')
        self.tabs.setIconSize(QSize(14, 14))
        self.tabs.setDrawBase(False)
        pages = QStackedWidget()
        self.appearance = AppearancePage(owner, pets)
        self.play = PlayPage(owner)
        self.options = OptionsPage(owner)
        tab_tips = (
            'Choose companion, colour palette, size, and movement speed (Alt+1)',
            'Interact, launch toys or focus sessions, and play poses (Alt+2)',
            'Configure movement, speech bubbles, window layer, and startup (Alt+3)',
        )
        for index, ((name, pattern, page), tip) in enumerate(zip(
                (('Appearance', PAW, self.appearance), ('Play', STAR, self.play),
                 ('Settings', SLIDERS, self.options)), tab_tips)):
            self.tabs.addTab(tab_icon(pattern), name)
            self.tabs.setTabToolTip(index, tip)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.viewport().setObjectName('controlsViewport')
            page.setObjectName('controlsPage')
            page.setAttribute(Qt.WA_StyledBackground)
            scroll.setWidget(page)
            pages.addWidget(scroll)
        self.tabs.currentChanged.connect(pages.setCurrentIndex)
        navigation = QHBoxLayout()
        navigation.setSpacing(8)
        navigation.addWidget(self.tabs, 1)
        close = QPushButton('Close', objectName='closeZoo')
        close.setAccessibleName('Close zoo menu')
        close.setToolTip('Close menu (Esc)')
        close.setMinimumWidth(68)
        close.clicked.connect(self.hide)
        navigation.addWidget(close)
        layout.addLayout(navigation)
        layout.addWidget(pages, 1)
        for button in self.findChildren(QPushButton):
            button.setAutoDefault(False)
            button.setCursor(Qt.PointingHandCursor)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if mods & Qt.AltModifier and key in (Qt.Key_1, Qt.Key_2, Qt.Key_3):
            self.tabs.setCurrentIndex(key - Qt.Key_1)
            return
        if mods & Qt.ControlModifier and key in (Qt.Key_Tab, Qt.Key_Backtab):
            step = -1 if key == Qt.Key_Backtab or (mods & Qt.ShiftModifier) else 1
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + step) % self.tabs.count())
            return
        super().keyPressEvent(event)

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

    def _status_summary(self):
        owner = self.owner
        data = owner.companion.data
        if owner.settings.data['paused']:
            return 'paused', 'Paused', 'Animations and roaming are paused in Settings'
        if data['sleeping']:
            return 'sleeping', 'Napping', 'Resting to recharge energy'
        if data['focus_until'] is not None:
            minutes, seconds = divmod(owner.companion.remaining(), 60)
            return 'focus', f'Focus {minutes:02d}:{seconds:02d}', 'Focus timer is running'
        if owner.firefly.active:
            return 'play', 'Firefly hunt', 'Firefly hunt is active on your desktop'
        if owner.ball.active:
            return 'play', 'Chasing yarn', 'Yarn ball is active on your desktop'
        if getattr(owner, 'follow_until', 0) > 0:
            import time
            left = max(0, int(owner.follow_until - time.monotonic()))
            if left > 0:
                return 'play', f'Following ({left}s)', 'Following your pointer across the screen'
        return 'active', 'Ready', 'Active on your desktop'

    def sync_live(self):
        pet = self.owner.settings.data['pet']
        companion = self.owner.companion
        d = companion.data
        self.name.setText(d['name'])
        level, earned, required = companion.friendship_progress
        self.details.setText(f'{self.pets[pet]}  ·  Level {level}  ·  {required - earned} XP to level {level + 1}')
        self.progress.setRange(0, required)
        self.progress.setValue(earned)
        self.progress.setToolTip(f"{d['xp']} total XP · {earned} / {required} XP toward level {level + 1}")
        self.mood.setText(companion.mood_for(pet))
        self.care_summary.setText(
            f"Love {round(d['affection'])}%  ·  Snacks {round(d['fullness'])}%  ·  Energy {round(d['energy'])}%"
        )
        state, badge_text, badge_tip = self._status_summary()
        self.status_badge.setText(badge_text)
        self.status_badge.setToolTip(badge_tip)
        if state != self._last_badge_state:
            self._last_badge_state = state
            self.status_badge.setProperty('state', state)
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
        wave_hint = ' · click preview to wave' if self.owner.ready_for_trick() else ''
        self.preview.setToolTip(f"{d['name']} ({self.pets[pet]}){wave_hint}")
        self.play.sync()

    def set_frame(self, frame):
        self.preview.frame = frame
        self.preview.update()
