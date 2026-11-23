"""Paint a narrow foliage border around the pet menus."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen


def _leaf(painter, start, tip, width, color):
    direction = tip - start
    size = math.hypot(direction.x(), direction.y())
    normal = QPointF(-direction.y(), direction.x()) * (width / size)
    shape = QPainterPath(start)
    shape.cubicTo(start + direction * .23 + normal,
                  start + direction * .64 + normal * .82, tip)
    shape.cubicTo(start + direction * .64 - normal * .66,
                  start + direction * .27 - normal * .75, start)
    painter.fillPath(shape, QColor(color))


def _twig(painter, start, end):
    shape = QPainterPath(start)
    shape.quadTo(QPointF(start.x(), end.y()), end)
    painter.drawPath(shape)


def _corner(painter, span, trail):
    stem = QPainterPath(QPointF(span, 3))
    stem.cubicTo(span * .72, 0, span * .48, 7, span * .27, 4)
    stem.cubicTo(10, 2, 3, 9, 4, 18)
    stem.cubicTo(7, trail * .52, 2, trail * .75, 6, trail)
    painter.setPen(QPen(QColor('#5c8850'), 1.25, Qt.SolidLine, Qt.RoundCap))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(stem)

    for start, tip in (
        (QPointF(span * .34, 4), QPointF(span * .38, 8)),
        (QPointF(5, trail * .48), QPointF(10, trail * .53)),
        (QPointF(5, trail * .80), QPointF(9, trail * .86)),
    ):
        _twig(painter, start, tip)

    leaves = (
        ((span * .86, 3), (span * .98, 6), 2.1, '#79a76a'),
        ((span * .72, 3), (span * .59, 1), 1.8, '#588c5e'),
        ((span * .62, 4), (span * .50, 10), 2.3, '#699d62'),
        ((span * .45, 5), (span * .32, 1), 1.9, '#79a76a'),
        ((span * .23, 4), (span * .15, 9), 1.9, '#588c5e'),
        ((4, 14), (12, 10), 2.5, '#79a76a'),
        ((5, trail * .34), (12, trail * .30), 2.2, '#699d62'),
        ((5, trail * .59), (2, trail * .68), 1.8, '#588c5e'),
        ((5, trail * .70), (13, trail * .74), 2.4, '#79a76a'),
        ((6, trail * .94), (3, trail), 1.5, '#699d62'),
    )
    for start, tip, width, color in leaves:
        _leaf(painter, QPointF(*start), QPointF(*tip), width, color)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor('#c4a461'))
    for x, y in ((span * .38, 8), (10, trail * .53), (9, trail * .86)):
        painter.drawEllipse(QPointF(x, y), 1.4, 1.4)


def paint_vines(painter, rect, *, compact=False):
    """Frame the top corners within the first 12 px above and 15 px beside the content."""
    area = QRectF(rect)
    if area.width() < 42 or area.height() < 36:
        return

    span = min(area.width() * .36, 50 if compact else 128)
    trail = min(area.height() * .58, 44 if compact else 165)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setClipRect(area, Qt.IntersectClip)
    painter.translate(area.left() + 1, area.top() + 1)
    _corner(painter, span, trail)
    painter.translate(area.width() - 2, 0)
    painter.scale(-1, 1)
    _corner(painter, span, trail * .86)
    painter.restore()
