"""Screen bounds for desktop routes and nearby pet activity."""
from PySide6.QtCore import QPoint, QRect

# Keep routines and wandering a few pixels inside the usable area so a pet
# never clips the panel or the screen edge while it plays.
EDGE_MARGIN = 12


def _clamp(value, low, high):
    return max(low, min(high, value))


def _edge_margin(screen):
    """A margin that still leaves room on very small or oddly shaped screens."""
    return min(EDGE_MARGIN, max(0, min(screen.width(), screen.height()) // 10))


def top_left_bounds(pet, screen, margin=0):
    """Return the inclusive range where the whole pet fits on screen."""
    left, top = screen.left() + margin, screen.top() + margin
    right, bottom = screen.right() - margin, screen.bottom() - margin
    return left, top, max(left, right - pet.width() + 1), max(top, bottom - pet.height() + 1)


def bounded_position(point, bounds):
    left, top, right, bottom = bounds
    return QPoint(max(left, min(right, point.x())), max(top, min(bottom, point.y())))


def nearby_play_area(pet, screen):
    """Keep a short routine or toy chase within reach of its starting point.

    The stage stays a comfortable size, follows the pet across its display and
    leaves headroom above the pet plus a little floor below, so jumps and
    pounces never end against a screen edge.
    """
    gap = _edge_margin(screen)
    left, top = screen.left() + gap, screen.top() + gap
    right, bottom = screen.right() - gap, screen.bottom() - gap
    room_width, room_height = max(1, right - left + 1), max(1, bottom - top + 1)
    width = min(room_width, max(394, pet.width() * 2 + 72))
    height = min(room_height, max(276, pet.height() + 164))
    x = _clamp(pet.center().x() - width // 2, left, right - width + 1)
    y = _clamp(pet.bottom() - height * 2 // 3, top, bottom - height + 1)
    return QRect(x, y, width, height)
