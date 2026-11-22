"""Screen bounds for nearby pet activity."""
from PySide6.QtCore import QRect


def roaming_area(pet, screen):
    """Fit a small roaming area around the pet inside its current screen."""
    width = min(screen.width(), max(394, pet.width() * 2 + 72))
    height = min(screen.height(), max(276, pet.height() + 164))
    x = max(screen.left(), min(pet.center().x() - width // 2, screen.right() - width + 1))
    y = max(screen.top(), min(pet.bottom() - height + 1, screen.bottom() - height + 1))
    return QRect(x, y, width, height)
