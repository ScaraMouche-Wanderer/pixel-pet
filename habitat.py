"""Screen bounds for nearby pet activity."""
from PySide6.QtCore import QPoint, QRect


def top_left_bounds(widget, screen):
    """Return the inclusive range where the whole widget fits on screen."""
    left, top = screen.left(), screen.top()
    return left, top, max(left, screen.right() - widget.width() + 1), max(top, screen.bottom() - widget.height() + 1)


def bounded_position(point, bounds):
    left, top, right, bottom = bounds
    return QPoint(max(left, min(right, point.x())), max(top, min(bottom, point.y())))


def roaming_area(pet, screen):
    """Fit a small roaming area around the pet inside its current screen."""
    width = min(screen.width(), max(394, pet.width() * 2 + 72))
    height = min(screen.height(), max(276, pet.height() + 164))
    x = max(screen.left(), min(pet.center().x() - width // 2, screen.right() - width + 1))
    y = max(screen.top(), min(pet.bottom() - height + 1, screen.bottom() - height + 1))
    return QRect(x, y, width, height)
