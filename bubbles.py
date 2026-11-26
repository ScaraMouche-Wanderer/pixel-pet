"""Pixel speech bubbles drawn to fit the active desktop screen."""
from dataclasses import dataclass

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygon, QTextLayout, QTextOption


MOON = ('0011000', '0110000', '1100000', '1100001', '1110011', '0111110', '0011100')
PAW = ('0101010', '0101010', '0000000', '1011101', '0111110', '0111110', '0011100')
BANANA = ('0000010', '0000110', '0000110', '1001110', '1111100', '0111000', '0000000')
FEATHER = ('0000111', '0001111', '0011100', '0111110', '1111000', '1100000', '1000000')
STAR = ('0001000', '0011100', '1111111', '0111110', '0011100', '0110110', '0000000')

# Background, outline, and icon color for Original, Pastel, and Moonlight.
PALETTES = {
    'cat': (MOON, (('#24223e', '#a293fa', '#bdf2ed'), ('#37263c', '#dc9ec8', '#ffe6f6'),
                   ('#172d3a', '#70b4c9', '#a4f3df'))),
    'cat-classic': (PAW, (('#392822', '#f5b67e', '#ffd6a4'), ('#3d2935', '#e2a1ba', '#ffdbce'),
                          ('#252944', '#a9b2ea', '#ffc6db'))),
    'monkey': (BANANA, (('#283326', '#9cc78c', '#ffda75'), ('#3a2936', '#e1a2bc', '#ffe7a9'),
                       ('#25243f', '#9f96d5', '#a5efd8'))),
    'eagle': (FEATHER, (('#1b2b3a', '#89b9d6', '#ffd398'), ('#303045', '#b6adda', '#ffd7c2'),
                        ('#182b44', '#8db5e8', '#ffdc97'))),
    'mascot': (STAR, (('#292637', '#b9a5f5', '#ffe6a7'),) * 3),
}
STYLE_INDEX = {'original': 0, 'pastel': 1, 'night': 2}


@dataclass
class BubbleText:
    font: QFont
    lines: tuple[str, ...]
    width: int
    height: int
    line_height: int


def theme_for(pet, style):
    icon, colors = PALETTES.get(pet, PALETTES['mascot'])
    return icon, colors[STYLE_INDEX.get(style, 0)]


def fit_text(message, available_width):
    font = QFont('DejaVu Sans', 10)
    metrics = QFontMetrics(font)
    message = ' '.join(message.split())
    # Leave room for the icon and padding, even if the screen is very narrow.
    maximum = max(20, min(298, available_width - 10))
    width = min(maximum, max(94, metrics.horizontalAdvance(message) + 47))
    line_width = max(5, width - 46)
    layout = QTextLayout(message, font)
    options = QTextOption()
    options.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
    layout.setTextOption(options)
    utf16 = message.encode('utf-16-le', 'surrogatepass')
    lines = []
    layout.beginLayout()
    for index in range(3):
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(line_width)
        start = line.textStart() * 2
        end = start + line.textLength() * 2
        if index == 2 and end < len(utf16):
            remainder = utf16[start:].decode('utf-16-le', 'replace')
            lines.append(metrics.elidedText(remainder, Qt.ElideRight, line_width))
        else:
            lines.append(utf16[start:end].decode('utf-16-le', 'replace').strip())
    layout.endLayout()
    return BubbleText(font, tuple(lines), width, max(30, 14 + len(lines) * metrics.lineSpacing()),
                      metrics.lineSpacing())


def bubble_position(art, screen, text):
    inset = 5
    gap = 14
    above_y = art.top() - text.height - gap
    below_y = art.bottom() + gap
    above = above_y >= screen.top() + inset or below_y + text.height > screen.bottom() - inset
    x = max(screen.left() + inset,
            min(art.center().x() - text.width // 2, screen.right() - text.width - inset + 1))
    y = above_y if above else below_y
    y = max(screen.top() + inset, min(y, screen.bottom() - text.height - inset + 1))
    box = QRect(x, y, text.width, text.height)
    tip = max(box.left() + 12, min(art.center().x(), box.right() - 12))
    return box, above, tip


def paint_bubble(painter, box, above, tip, text, theme, draw_icon):
    icon, (fill, border, accent) = theme
    x, y, r, b = box.left(), box.top(), box.right(), box.bottom()
    step = 5
    top_tail = [] if above else [(tip - 6, y), (tip, y - 7), (tip + 6, y)]
    bottom_tail = [(tip + 6, b), (tip, b + 7), (tip - 6, b)] if above else []
    points = [(x + step, y), *top_tail, (r - step, y), (r, y + step), (r, b - step),
              (r - step, b), *bottom_tail, (x + step, b), (x, b - step), (x, y + step)]
    shape = QPolygon([QPoint(px, py) for px, py in points])
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(8, 9, 18, 145))
    painter.drawPolygon(shape.translated(2, 3))
    painter.setPen(QPen(QColor(border), 2))
    painter.setBrush(QColor(fill))
    painter.drawPolygon(shape)
    draw_icon(painter, icon, x + 12, y + (box.height() - 14) // 2, accent, 2)
    painter.setFont(text.font)
    painter.setPen(QColor('#fff7f1'))
    painter.setRenderHint(QPainter.TextAntialiasing)
    ascent = QFontMetrics(text.font).ascent()
    top = y + (box.height() - len(text.lines) * text.line_height) // 2
    for index, line in enumerate(text.lines):
        painter.drawText(QPointF(x + 36, top + ascent + index * text.line_height), line)
