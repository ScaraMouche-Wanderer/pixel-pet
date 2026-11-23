"""Pixel-snapped body animation layered over the pets' original pose frames."""
from math import cos, pi, sin, tau
from typing import NamedTuple

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QPainter, QPixmap, QRegion, QTransform

from pet_moves import MOVE_DURATION


class Beat(NamedTuple):
    x: float = 0
    lift: float = 0
    lean: float = 0
    squash: float = 0


# Wind-up, main gesture, follow-through and landing. Distances are fractions
# of the silhouette, angles are degrees, and positive squash lowers the body.
BEATS = {
    'cat': (Beat(-.04, 0, -8, .12), Beat(.10, .14, 9, -.09), Beat(.06, .07, -5), Beat(0, 0, 3, .10)),
    'cat-classic': (Beat(-.06, 0, 5, .18), Beat(.15, .09, -12, -.06), Beat(.11, .03, 7), Beat(-.02, 0, -4, .12)),
    'monkey': (Beat(-.10, .01, -19, .08), Beat(.12, .16, 26, -.12), Beat(-.08, .10, -21), Beat(.03, 0, 9, .14)),
    'eagle': (Beat(-.04, .02, -9, .08), Beat(.10, .19, -16, -.05), Beat(.16, .03, 19), Beat(.04, .07, -6)),
    'owl': (Beat(0, 0, -13, .10), Beat(-.07, .15, -7, -.06), Beat(.11, .10, 10), Beat(.02, 0, -4, .11)),
    'hoots': (Beat(.02, 0, 16, .16), Beat(-.08, .14, -18, -.08), Beat(.07, .08, 14), Beat(0, 0, -9, .14)),
    'codex': (Beat(-.02, 0, -5, .07), Beat(.07, .07, 4), Beat(-.04, .07, -3), Beat(0, 0, 1, .06)),
    'dewey': (Beat(0, 0, -5, .25), Beat(.04, .19, 5, -.19), Beat(-.03, .08, -5, -.08), Beat(0, 0, 0, .27)),
    'fireball': (Beat(-.06, 0, -13, .14), Beat(.08, .20, 17, -.15), Beat(-.04, .12, -11, -.06), Beat(.01, 0, 6, .10)),
    'rocky': (Beat(-.04, 0, -12, .03), Beat(.08, .06, 19, -.02), Beat(.12, 0, 26), Beat(.03, .02, -8)),
    'seedy': (Beat(-.03, 0, -14, .08), Beat(.04, .05, 18, -.06), Beat(-.03, .02, -13), Beat(.01, 0, 7)),
    'stacky': (Beat(.02, 0, 12, .13), Beat(-.07, .12, -21, -.11), Beat(.06, .05, 17), Beat(-.02, 0, -8, .15)),
    'bsod': (Beat(0, 0, -3, .06), Beat(-.08, .07, -7, -.03), Beat(.07, .03, 6), Beat(-.02, 0, -3)),
    'null-signal': (Beat(-.05, .02, -6), Beat(.11, .09, 9, -.07), Beat(-.09, .05, -10), Beat(.03, .03, 3)),
}

STEPS = 36


def body_beat(pet, path, step):
    times = (0, 7, 15, 23, 29, STEPS - 1)
    poses = (Beat(), *BEATS[pet], Beat())
    segment = next(i for i, end in enumerate(times[1:]) if step <= end)
    t = (step - times[segment]) / (times[segment + 1] - times[segment])
    t = t * t * (3 - 2 * t)
    x, lift, lean, squash = (a + (b - a) * t for a, b in zip(poses[segment], poses[segment + 1]))
    phase = step / (STEPS - 1)
    envelope = sin(pi * phase) ** 2
    if path in ('spiral', 'orbit', 'flutter', 'ribbon'):
        lean += 8 * sin(tau * phase * 2) * envelope
    elif path in ('arc', 'bounce', 'juggle', 'splash'):
        lift += .07 * abs(sin(tau * phase)) * envelope
    elif path in ('type', 'scan', 'scurry'):
        x += .035 * (1 if cos(tau * phase * 4) > 0 else -1) * envelope
    return Beat(x, lift, lean, squash)


def body_transform(size, bounds, beat):
    pivot = QPointF(bounds.center().x(), bounds.bottom())
    transform = QTransform()
    transform.translate(pivot.x() + round(bounds.width() * beat.x),
                        pivot.y() - round(bounds.height() * beat.lift))
    transform.rotate(beat.lean)
    transform.scale(1 + beat.squash * .5, 1 - beat.squash)
    transform.translate(-pivot.x(), -pivot.y())
    # Keep tall sprites and wide wingbeats inside the native surface.
    box = transform.mapRect(bounds).adjusted(-1, -1, 1, 1)
    fit = min(1., size.width() / box.width(), size.height() / box.height())
    transform *= QTransform.fromScale(fit, fit)
    box = transform.mapRect(bounds)
    dx = max(0, -box.left()) + min(0, size.width() - 1 - box.right())
    dy = max(0, -box.top()) + min(0, size.height() - 1 - box.bottom())
    return transform * QTransform.fromTranslate(dx, dy)


class IdleMotion:
    """Small, cached breathing poses, with a stable input shape even between blinks."""

    def __init__(self, sprites):
        self.frames = {}
        self.transforms = {}
        self.envelope = QRegion()
        self.sprites = sprites
        row, durations = sprites.animations['idle']
        rest = BEATS[sprites.pet][0]
        for column in range(len(durations)):
            source = sprites.frame(row, column)
            mask = sprites.masks[row, column]
            for phase in range(5):
                amount = phase / 4
                beat = Beat(0, 0, rest.lean * .18 * amount, rest.squash * .26 * amount)
                transform = body_transform(source.size(), mask.boundingRect(), beat)
                self.transforms[column, phase] = transform
                self.envelope |= transform.map(mask)

    def frame(self, row, column, phase):
        key = column, phase
        if key not in self.frames:
            source = self.sprites.frame(row, column)
            if phase == 0:
                return source
            frame = QPixmap(source.size())
            frame.fill(Qt.transparent)
            painter = QPainter(frame)
            painter.setTransform(self.transforms[key])
            painter.drawPixmap(0, 0, source)
            painter.end()
            self.frames[key] = frame
        return self.frames[key]


def perform_frames(sprites, move):
    row, durations = sprites.animations[move.pose]
    frames = []
    envelope = QRegion()
    for step in range(STEPS):
        elapsed = step * MOVE_DURATION * 1000 / (STEPS - 1) % sum(durations)
        column = 0
        while elapsed >= durations[column] and column < len(durations) - 1:
            elapsed -= durations[column]
            column += 1
        source = sprites.frame(row, column)
        mask = sprites.masks[row, column]
        beat = body_beat(sprites.pet, move.path, step)
        transform = body_transform(source.size(), mask.boundingRect(), beat)
        frame = QPixmap(source.size())
        frame.fill(Qt.transparent)
        painter = QPainter(frame)
        painter.setTransform(transform)
        # Stacky's tiers settle a beat apart. The signal pets occasionally
        # slip a horizontal scanline sideways during their main gesture.
        bounds = mask.boundingRect()
        slices = []
        if sprites.pet == 'stacky':
            for tier in range(3):
                top = bounds.top() + bounds.height() * tier // 3
                bottom = bounds.top() + bounds.height() * (tier + 1) // 3
                shift = round((2 - tier) * bounds.width() * beat.lean / 380)
                slices.append((QRect(bounds.x(), top, bounds.width(), bottom - top), shift))
        elif sprites.pet in ('null-signal', 'bsod') and step in (10, 11, 22, 24):
            top = bounds.top() + bounds.height() * (2 if step < 20 else 4) // 7
            band = max(1, bounds.height() // 11)
            shift = round(bounds.width() * (.055 if step % 2 else -.055))
            slices = [(QRect(bounds.x(), bounds.y(), bounds.width(), top - bounds.y()), 0),
                      (QRect(bounds.x(), top, bounds.width(), band), shift),
                      (QRect(bounds.x(), top + band, bounds.width(), bounds.bottom() + 1 - top - band), 0)]
        if slices:
            sliced_mask = QRegion()
            for rect, shift in slices:
                painter.drawPixmap(rect.topLeft() + QPoint(shift, 0), source, rect)
                sliced_mask |= (mask & QRegion(rect)).translated(shift, 0)
            mask = sliced_mask
        else:
            painter.drawPixmap(0, 0, source)
        painter.end()
        frames.append(frame)
        envelope |= transform.map(mask)
    return frames, envelope
