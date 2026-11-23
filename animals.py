"""Original raster sprites and short desktop outings for the animal companions."""
import math
import random

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QPolygon

STYLES = {'original': 'Original', 'pastel': 'Pastel', 'night': 'Moonlight'}
TRICKS = {'cat': 'Chase yarn', 'cat-classic': 'Chase yarn',
          'monkey': 'Climb an edge', 'eagle': 'Take flight',
          'owl': 'Take flight', 'hoots': 'Take flight'}
FLYERS = ('eagle', 'owl', 'hoots')
SHOWTIME = {'cat': 'Comet pounce', 'monkey': 'Cartwheel dash', 'eagle': 'Sky corkscrew'}
PLAY_PACES = {'gentle': ('Gentle', .375), 'normal': ('Normal', .5), 'zoomies': ('Zoomies', .64)}
ACTIVITIES = {
    'cat': ('yarn', 'prowl', 'pounce', 'cat-show', 'cat-stretch', 'cat-groom'),
    'monkey': ('climb', 'scamper', 'hop', 'monkey-show', 'monkey-swing', 'monkey-hang'),
    'eagle': ('eagle-flight', 'swoop', 'hop', 'eagle-show', 'bird-preen'),
    'owl': ('owl-flight', 'bird-preen', 'hop'),
    'hoots': ('hoots-flight', 'bird-preen', 'hop'),
}
IDLE_MOVES = {'cat-stretch': ('stretch', 1.55), 'cat-groom': ('groom', 1.9),
              'monkey-hang': ('tail-hang', 1.52), 'bird-preen': ('preen', 1.64)}
ANIMAL_ROWS = {
    'idle': (0, [2300, 350, 140]),
    'running-right': (1, [100, 145, 115, 155]),
    'running-left': (2, [100, 145, 115, 155]),
    'waving': (3, [180, 200, 230, 260]),
    'jumping': (4, [160, 170, 160, 220]),
    'review': (5, [160, 180, 180, 280]),
    'waiting': (6, [500, 260]),
    'failed': (7, [360, 270]),
    'running': (1, [150] * 4),
    'trick-right': (8, [135] * 4),
    'trick-left': (9, [135] * 4),
    'stunt-right': (10, [92] * 8),
    'stunt-left': (11, [92] * 8),
}
MONKEY_ROWS = {
    'swing-right': (12, [108, 136, 116, 140]),
    'swing-left': (13, [108, 136, 116, 140]),
    'tail-hang': (14, [160, 400, 200, 300]),
}
BIRD_ROWS = {
    'trick-takeoff-right': (12, [110, 105, 130, 110]),
    'trick-takeoff-left': (13, [110, 105, 130, 110]),
    'trick-glide-right': (14, [170, 230, 160, 240]),
    'trick-glide-left': (15, [170, 230, 160, 240]),
    'trick-flap-right': (16, [95, 120, 145, 105]),
    'trick-flap-left': (17, [95, 120, 145, 105]),
    'trick-land-right': (18, [150, 150, 180, 200]),
    'trick-land-left': (19, [150, 150, 180, 200]),
    'preen': (20, [190, 230, 210, 230]),
}
EXTRA_ANIMATIONS = {
    'cat': (('stretch', 'Stretch'), ('groom', 'Groom')),
    'monkey': (('swing-right', 'Swing'), ('tail-hang', 'Hang by the tail')),
    'eagle': (('trick-flap-right', 'Flap wings'), ('preen', 'Preen feathers')),
    'owl': (('trick-flap-right', 'Flutter wings'), ('preen', 'Preen feathers')),
    'hoots': (('trick-flap-right', 'Flutter wings'), ('preen', 'Preen feathers')),
}
PALETTES = {
    'monkey': {
        'original': ('#422731', '#79483e', '#a96549', '#f5bf8b', '#fa8988', '#f8dc8f'),
        'pastel': ('#64405e', '#ab668d', '#d887af', '#ffc9cc', '#ec779d', '#ffeab4'),
        'night': ('#29213e', '#473d76', '#6e61a3', '#c5aae6', '#ec9fcb', '#93e8d5'),
    },
    'eagle': {
        'original': ('#382b38', '#645047', '#947158', '#fff0d9', '#ee9b53', '#f3bc55'),
        'pastel': ('#413f63', '#6c6796', '#9291c5', '#faf1fc', '#dc8da2', '#ffbd76'),
        'night': ('#222a44', '#344a73', '#5878a2', '#cfe9ff', '#8eb9f4', '#ffcd7f'),
    },
    'owl': {
        'original': ('#233941', '#315966', '#639091', '#f1dda5', '#e5a86b', '#f9c963'),
        'pastel': ('#493651', '#765579', '#ab85a9', '#ffe5cc', '#eba3ac', '#f5ca83'),
        'night': ('#242b49', '#3b4c77', '#6885a9', '#c5e6e6', '#d5a9c6', '#f4c782'),
    },
}


def animal_frame(animal, style, row, column):
    image = QImage(40, 40, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    colors = [QColor(color) for color in PALETTES[animal][style]]
    painter = QPainter(image)
    painter.setPen(Qt.NoPen)
    painter.translate(0, 2)
    if row in (2, 9, 11, 13, 15, 17, 19):
        painter.translate(40, 0)
        painter.scale(-1, 1)
    if row in (10, 11) or (animal == 'monkey' and row == 14):
        painter.translate(20, 18)
        painter.scale(.73, .73)
        angle = (135, 180, 173, 188)[column] if row == 14 else column * 45
        painter.rotate(angle)
        painter.translate(-20, -18)
        row, column = (8 if row == 14 else 4 if animal == 'monkey' else 8), column % 4
    if animal == 'monkey' and row in (12, 13):
        painter.translate(20, 16)
        painter.scale(.83, .83)
        painter.rotate((-21, 6, 24, 10)[column])
        painter.translate(-20, -16)
        row = 8
    if animal == 'monkey':
        draw_monkey(painter, colors, row, column)
    elif animal == 'owl':
        draw_dusk_owl(painter, colors, row, column)
    else:
        draw_eagle(painter, colors, row, column)
    painter.end()
    return QPixmap.fromImage(image)


def poly(painter, color, *points):
    painter.setBrush(color)
    painter.drawPolygon(QPolygon([QPoint(x, y) for x, y in points]))


def ellipse(painter, color, x, y, w, h):
    painter.setBrush(color)
    painter.drawEllipse(x, y, w, h)


def draw_monkey(p, colors, row, col):
    ink, shadow, fur, face, pink, gold = colors
    climbing = row in (8, 9)
    moving = row in (1, 2)
    sleeping = row == 0 and col == 3
    waving = row in (3, 5)
    if row == 4:
        p.translate(0, -(0, 2, 4, 2)[col])
    elif moving or waving:
        p.translate(0, -(0, 1, 2, 1)[col])
    # Curled tail with the open center kept transparent.
    p.setPen(Qt.PenStyle.NoPen)
    p.save()
    if moving:
        p.translate(0, (0, -2, 0, 2)[col])
    poly(p, ink, (14, 25), (8, 28), (4, 27), (2, 23), (3, 19), (6, 16),
         (10, 16), (12, 18), (12, 21), (10, 24), (7, 24), (6, 22), (7, 20),
         (9, 20), (9, 19), (7, 19), (5, 21), (5, 24), (8, 25), (13, 22))
    poly(p, fur, (12, 24), (8, 27), (4, 25), (3, 22), (5, 18), (7, 17),
         (10, 17), (11, 19), (11, 21), (9, 23), (7, 23), (7, 22), (9, 22),
         (10, 20), (9, 18), (7, 18), (4, 21), (4, 24), (8, 26), (12, 23))
    p.restore()
    ellipse(p, ink, 11, 19, 20, 16)
    ellipse(p, shadow, 12, 20, 18, 14)
    ellipse(p, fur, 15, 21, 13, 11)
    ellipse(p, face, 17, 23, 10, 8)
    foot = (0, 3, 0, -3)[col] if moving or climbing else 0
    for x, delta in ((12, foot), (22, -foot)):
        ellipse(p, ink, x + delta, 30, 9, 6)
        ellipse(p, fur, x + delta + 1, 31, 7, 4)
    if climbing:
        up = (2, 6, 9, 5)[col]
        poly(p, ink, (26, 22), (35, up + 10), (39, up + 9), (39, up + 15),
             (34, up + 16), (30, 27), (25, 28))
        poly(p, fur, (27, 23), (36, up + 11), (38, up + 10), (38, up + 14),
             (33, up + 15), (29, 26), (26, 26))
        ellipse(p, face, 35, up + 10, 4, 4)
    elif waving:
        up = (2, 5, 6, 4)[col]
        ellipse(p, ink, 28, 21 - up, 8, 12)
        ellipse(p, fur, 29, 22 - up, 6, 10)
        ellipse(p, face, 30, 21 - up, 5, 5)
    else:
        sway = (0, 2, 0, -2)[col] if moving else 0
        ellipse(p, ink, 26 + sway, 22, 8, 9)
        ellipse(p, fur, 27 + sway, 23, 6, 7)
    # Big ears, cheek patches, and a tiny tuft.
    ellipse(p, ink, 9, 10, 10, 11)
    ellipse(p, ink, 26, 10, 11, 11)
    ellipse(p, fur, 10, 11, 8, 9)
    ellipse(p, fur, 27, 11, 9, 9)
    ellipse(p, pink, 12, 13, 5, 6)
    ellipse(p, pink, 30, 13, 5, 6)
    ellipse(p, ink, 13, 5, 20, 22)
    ellipse(p, fur, 14, 6, 18, 20)
    poly(p, ink, (18, 8), (18, 4), (21, 5), (23, 2), (26, 5), (28, 8))
    poly(p, fur, (19, 8), (19, 5), (21, 6), (23, 3), (25, 6), (27, 8))
    ellipse(p, face, 15, 11, 16, 14)
    ellipse(p, face, 16, 9, 8, 10)
    ellipse(p, face, 23, 9, 7, 10)
    blink = sleeping or row in (5, 7) or (row == 0 and col == 2)
    for x in (18, 25):
        p.fillRect(x, 15, 3, 1 if blink else 4, ink)
        if not blink:
            p.fillRect(x + 1, 15, 1, 1, QColor('#fff8ec'))
    p.fillRect(16, 20, 3, 1, pink)
    p.fillRect(27, 20, 3, 1, pink)
    p.fillRect(22, 20, 2, 1, shadow)
    p.fillRect(21, 22, 4, 1, ink)
    p.fillRect(22, 23, 2, 1, ink)
    if row in (3, 5) and col in (1, 2):
        p.fillRect(33, 7, 3, 1, gold)
        p.fillRect(34, 6, 1, 3, gold)


def draw_eagle(p, colors, row, col):
    ink, shadow, wing, ivory, blush, gold = colors
    phase = (row - 12) // 2 if 12 <= row < 20 else None
    flight = row in (8, 9) or phase is not None
    preening = row == 20
    hopping = row == 4
    moving = row in (1, 2)
    if hopping:
        p.translate(0, -(0, 2, 4, 2)[col])
    elif flight or moving:
        p.translate(0, -(0, 1, 2, 1)[col])
    if flight:
        wing_positions = ((7, 2, 20, 9), (11, 12, 10, 12), (2, 13, 24, 11), (6, 11, 16, 22))
        tip = ((5, 13, 24, 14) if phase is None else wing_positions[phase])[col]
        poly(p, ink, (20, 15), (13, tip + 2), (5, tip), (0, tip + 1), (2, tip + 6),
             (8, tip + 10), (16, 23), (23, 25))
        poly(p, wing, (20, 16), (12, tip + 4), (2, tip + 2), (4, tip + 6),
             (9, tip + 10), (16, 22), (22, 24))
        poly(p, ink, (22, 19), (29, tip + 2), (36, tip), (39, tip + 1), (38, tip + 6),
             (33, tip + 11), (26, 23))
        poly(p, wing, (22, 19), (30, tip + 3), (37, tip + 1), (38, tip + 2),
             (36, tip + 6), (32, tip + 10), (26, 22))
    poly(p, ink, (8, 23), (19, 25), (16, 34), (5, 34), (7, 31), (4, 30))
    poly(p, ivory, (9, 25), (17, 26), (15, 33), (7, 33), (9, 30), (6, 30))
    ellipse(p, ink, 10, 16, 23, 18)
    ellipse(p, shadow, 11, 17, 21, 16)
    ellipse(p, wing, 14, 18, 17, 13)
    if not flight:
        wing_up = 4 if row in (3, 5) and col in (1, 2) else 0
        if moving:
            wing_up = (0, 2, 0, -1)[col]
        elif preening:
            wing_up = (0, 3, 5, 2)[col]
        poly(p, ink, (13, 20), (21, 17 - wing_up), (24, 21), (22, 27), (13, 30), (9, 28))
        poly(p, wing, (14, 21), (21, 18 - wing_up), (23, 21), (21, 26), (12, 29), (10, 27))
        p.fillRect(13, 24, 6, 1, shadow)
        p.fillRect(12, 26, 5, 1, shadow)
    claw = (0, 2, 0, -2)[col] if moving else 0
    if not flight or phase == 3:
        for x, dx in ((15, claw), (24, -claw)):
            p.fillRect(x + dx, 31, 6, 5, ink)
            p.fillRect(x + dx + 1, 32, 4, 3, gold)
    if preening:
        p.translate((0, -2, -3, -1)[col], (0, 2, 4, 2)[col])
    poly(p, ink, (17, 8), (21, 5), (23, 2), (26, 5), (31, 5), (35, 9), (35, 17),
         (31, 22), (27, 20), (23, 22), (20, 19), (17, 19))
    poly(p, ivory, (18, 9), (22, 6), (23, 4), (26, 6), (31, 6), (34, 9), (34, 17),
         (31, 20), (27, 18), (23, 20), (21, 18), (18, 18))
    poly(p, ink, (32, 12), (36, 12), (39, 15), (38, 19), (36, 20), (36, 17), (33, 17))
    poly(p, gold, (33, 13), (36, 13), (38, 15), (37, 18), (37, 16), (33, 16))
    blink = row in (5, 7) or (row == 0 and col in (2, 3)) or (preening and col in (1, 2))
    p.fillRect(28, 11, 3, 1 if blink else 4, ink)
    if not blink:
        p.fillRect(29, 11, 1, 1, QColor('#ffffff'))
    p.fillRect(26, 16, 3, 1, blush)


def draw_dusk_owl(p, colors, row, col):
    ink, shade, plumage, face, blush, gold = colors
    phase = (row - 12) // 2 if 12 <= row < 20 else None
    moving = row in (1, 2, 4)
    preening = row == 20
    if moving:
        p.translate(0, -(0, 2, 4, 1)[col])
    if phase is not None:
        wing_y = ((11, 4, 23, 12), (11, 13, 10, 13),
                  (3, 13, 24, 10), (8, 12, 19, 24))[phase][col]
        bend = (0, 1, 2, 0)[col]
        for mirror in (False, True):
            p.save()
            if mirror:
                p.translate(40, 0)
                p.scale(-1, 1)
            poly(p, ink, (18, 21), (13, wing_y + 2), (2, wing_y), (1, wing_y + 4),
                 (5, wing_y + 10), (10, wing_y + 10 + bend), (15, wing_y + 15), (20, 31))
            poly(p, plumage, (17, 21), (12, wing_y + 4), (3, wing_y + 2), (5, wing_y + 8),
                 (10, wing_y + 9 + bend), (15, wing_y + 13), (19, 28))
            p.fillRect(5, wing_y + 5, 7, 1, face)
            p.restore()
    ellipse(p, ink, 9, 14, 22, 22)
    ellipse(p, shade, 10, 15, 20, 20)
    ellipse(p, plumage, 13, 18, 14, 16)
    p.fillRect(16, 27, 8, 1, face)
    p.fillRect(18, 29, 4, 1, face)
    if phase is None or phase == 3:
        foot = (0, 1, 0, -1)[col] if moving else 0
        for x in (13 + foot, 23 - foot):
            p.fillRect(x, 33, 5, 3, ink)
            p.fillRect(x + 1, 34, 4, 1, gold)
    if preening:
        p.translate((0, -2, -3, 0)[col], (0, 1, 3, 1)[col])
    poly(p, ink, (8, 13), (8, 5), (13, 8), (17, 7), (23, 7), (27, 8),
         (32, 5), (32, 13), (33, 17), (30, 22), (25, 24), (15, 24), (9, 21), (7, 17))
    poly(p, plumage, (9, 13), (9, 7), (13, 10), (17, 8), (23, 8), (27, 10),
         (31, 7), (31, 13), (32, 17), (29, 21), (24, 23), (16, 23), (10, 20), (8, 17))
    ellipse(p, face, 10, 11, 10, 11)
    ellipse(p, face, 20, 11, 10, 11)
    eyes_closed = (row == 0 and col in (2, 3)) or row in (5, 7) or (preening and col in (1, 2))
    for x in (14, 23):
        p.fillRect(x, 14, 3, 1 if eyes_closed else 4, ink)
        if not eyes_closed:
            p.fillRect(x + 1, 14, 1, 1, QColor('#fff9e7'))
    p.fillRect(11, 19, 3, 1, blush)
    p.fillRect(26, 19, 3, 1, blush)
    poly(p, gold, (18, 17), (22, 17), (20, 21))


def owl_frame(body, row, column):
    """Animate a copy of the supplied owl frame with new pixel wing poses."""
    image = QImage(48, 52, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setPen(Qt.NoPen)
    if row == 20:
        painter.translate(24, 30)
        painter.rotate((0, -7, -12, -4)[column])
        painter.translate(-24, -30)
        painter.drawPixmap(0, (0, 2, 3, 1)[column], body.scaled(48, 49, Qt.KeepAspectRatio, Qt.FastTransformation))
    else:
        phase = (row - 12) // 2
        tips = ((18, 7, 35, 13), (18, 21, 18, 22), (6, 19, 36, 13), (11, 20, 28, 35))
        wing_y = tips[phase][column]
        for facing in (1, -1):
            painter.save()
            if facing < 0:
                painter.translate(48, 0)
                painter.scale(-1, 1)
            poly(painter, QColor('#8d461d'), (21, 28), (14, wing_y + 2), (2, wing_y), (1, wing_y + 4),
                 (4, wing_y + 11), (10, wing_y + 15), (19, wing_y + 16), (25, 35))
            poly(painter, QColor('#ef9239'), (21, 29), (13, wing_y + 4), (3, wing_y + 2),
                 (4, wing_y + 8), (11, wing_y + 13), (19, wing_y + 14), (24, 34))
            poly(painter, QColor('#ffcb78'), (7, wing_y + 6), (11, wing_y + 7),
                 (17, wing_y + 11), (11, wing_y + 10))
            painter.restore()
        owl = body.scaled(41, 44, Qt.KeepAspectRatio, Qt.FastTransformation)
        painter.drawPixmap(3 if row % 2 == 0 else 5, 4 + (0, 1, -1, 0)[column], owl)
    painter.end()
    return QPixmap.fromImage(image)


class Outing:
    """A randomized route with the original perch as the last waypoint."""
    def __init__(self, activity, geometry, available, now, pace=1.):
        self.activity = activity
        self.origin = geometry.topLeft()
        self.started = now
        x, y = self.origin.x(), self.origin.y()
        left, top = available.left(), available.top()
        right = max(left, available.right() - geometry.width() + 1)
        bottom = max(top, available.bottom() - geometry.height() + 1)
        self.bounds = (left, top, right, bottom)
        self.hop_height = random.randint(13, 29)
        side = 'left' if x - left <= right - x else 'right'
        if abs((x - left) - (right - x)) <= 140:
            side = random.choice(('left', 'right'))
        edge = left if side == 'left' else right
        x1 = left + round((right - left) * random.uniform(.10, .31))
        x2 = right - round((right - left) * random.uniform(.10, .31))
        if activity.endswith('-flight'):
            self.legs = self.flight(activity, top, bottom, right, left)
        elif activity in IDLE_MOVES:
            mode, duration = IDLE_MOVES[activity]
            self.legs = [(self.origin, duration, mode)]
        elif activity == 'monkey-swing':
            side = 'right' if side == 'left' else 'left'
            lead = QPoint(x2 if side == 'right' else x1, y)
            back = 'left' if side == 'right' else 'right'
            self.legs = [(lead, .94, 'swing-' + side), (self.origin, .87, 'swing-' + back),
                         (self.origin, .38, 'waving')]
        elif activity.endswith('-show'):
            self.legs = self.showtime(activity, x1, x2, top, bottom)
        elif activity in ('prowl', 'scamper'):
            first, second = (x1, x2) if side == 'right' else (x2, x1)
            self.legs = self.travel((QPoint(first, y), QPoint(second, y), self.origin),
                                    'running-', random.uniform(100, 165))
        elif activity in ('pounce', 'hop'):
            target = x1 if x - x1 > x2 - x else x2
            point = QPoint(target, y)
            self.legs = [(point, random.uniform(.65, .90), 'jumping'),
                         (point, random.uniform(.18, .50), 'waiting'),
                         *self.travel((self.origin,), 'running-', 130, start=point)]
        elif activity == 'climb':
            base_y = max(y, min(bottom, top + 140))
            high_y = max(top, base_y - max(75, round((bottom - top) * random.uniform(.21, .43))))
            side_mode = 'trick-' + side
            self.legs = [
                (QPoint(edge, base_y), max(.45, abs(edge - x) / 260), 'running-' + side),
                (QPoint(edge, high_y), max(.65, (base_y - high_y) / random.uniform(109, 162)), side_mode),
                (QPoint(edge, high_y), random.uniform(.22, .81), side_mode),
                (QPoint(edge, base_y), max(.65, (base_y - high_y) / 149), side_mode),
                (self.origin, max(.45, abs(edge - x) / 260),
                 'running-' + ('right' if side == 'left' else 'left')),
            ]
        else:
            near = QPoint(x1, top + round((bottom - top) * random.uniform(.12, .31)))
            far = QPoint(x2, top + round((bottom - top) * random.uniform(.12, .31)))
            first, second = (near, far) if side == 'left' else (far, near)
            if activity == 'swoop':
                second.setY(bottom - round((bottom - top) * .20))
            self.legs = self.travel((first, second, self.origin), 'trick-',
                                    random.uniform(280, 430) if activity == 'swoop' else random.uniform(155, 230))
        self.legs = [(point, duration / pace, mode) for point, duration, mode in self.legs]
        self.duration = sum(leg[1] for leg in self.legs)

    def flight(self, activity, top, bottom, right, left):
        x, y = self.origin.x(), self.origin.y()
        side = 1 if right - x >= x - left else -1
        owl = activity in ('owl-flight', 'hoots-flight')
        distance = min(right - x if side > 0 else x - left,
                       random.randint(350, 530) if owl else random.randint(530, 790))
        altitude = max(top + 8, y - (random.randint(145, 245) if owl else random.randint(225, 360)))
        if altitude >= y - 34:
            altitude = min(bottom, y + 81)
        outward = 'right' if side > 0 else 'left'
        homeward = 'left' if side > 0 else 'right'
        cruise = 'flap' if owl else 'glide'
        takeoff = QPoint(x + side * round(distance * .15), round(y + (altitude - y) * .55))
        far = QPoint(x + side * distance, altitude)
        approach = QPoint(x + side * round(distance * .14), round(y + (altitude - y) * .26))
        return [
            (self.origin, .2, 'waiting'),
            (takeoff, .54, 'trick-takeoff-' + outward),
            (far, max(.85, distance / (230 if owl else 315)), 'trick-' + cruise + '-' + outward),
            (far, .24, 'trick-flap-' + homeward),
            (approach, max(.85, distance / (245 if owl else 335)), 'trick-' + cruise + '-' + homeward),
            (self.origin, .57, 'trick-land-' + homeward),
        ]

    def showtime(self, activity, x1, x2, top, bottom):
        x, y = self.origin.x(), self.origin.y()
        target = x1 if x - x1 > x2 - x else x2
        side = 'left' if target < x else 'right'
        back = 'right' if target < x else 'left'
        destination = QPoint(target, y)
        if activity == 'cat-show':
            self.hop_height = 47
            return [(self.origin, .39, 'crouch-' + side), (destination, .58, 'jumping'),
                    (destination, .25, 'review'), (self.origin, .78, 'running-' + back)]
        if activity == 'monkey-show':
            return [(self.origin, .30, 'waiting'), (destination, .74, 'stunt-' + side),
                    (destination, .52, 'waving'), (self.origin, .80, 'running-' + back)]
        high = top + (bottom - top) // 5
        start_turn = QPoint(round((x + target) / 2), high)
        end_turn = QPoint(target, high + (bottom - top) // 5)
        return [(start_turn, .62, 'trick-' + side), (end_turn, .74, 'stunt-' + side),
                (QPoint(round((x + target) / 2), y), .55, 'trick-' + back),
                (self.origin, .42, 'running-' + back), (self.origin, .25, 'waving')]

    def travel(self, points, mode, speed, start=None):
        previous = self.origin if start is None else start
        legs = []
        for end in points:
            delta = end - previous
            legs.append((end, max(.38, math.hypot(delta.x(), delta.y()) / speed),
                         mode + ('right' if delta.x() >= 0 else 'left')))
            previous = end
        return legs

    def sample(self, now):
        elapsed = max(0., now - self.started)
        start = self.origin
        for end, duration, mode in self.legs:
            if elapsed < duration:
                f = elapsed / duration
                travel = .55 * f + .45 * f * f * (3 - 2 * f)
                x = round(start.x() + (end.x() - start.x()) * travel)
                y = round(start.y() + (end.y() - start.y()) * travel)
                if mode == 'jumping':
                    y -= round(self.hop_height * math.sin(math.pi * f))
                elif mode.startswith('stunt-'):
                    y -= round(18 * math.sin(math.pi * f))
                elif mode.startswith('swing-'):
                    y -= round(45 * math.sin(math.pi * f))
                elif mode.startswith(('trick-glide-', 'trick-flap-')):
                    y -= round(12 * math.sin(math.pi * f))
                left, top, right, bottom = self.bounds
                return QPoint(max(left, min(right, x)), max(top, min(bottom, y))), mode
            start = end
            elapsed -= duration
        return self.origin, None
