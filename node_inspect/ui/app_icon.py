"""Application icon generation for NodeInspect."""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRectF


def create_app_icon(size: int = 64) -> QIcon:
    """Generate a modern, clean NodeInspect logo icon dynamically."""
    icon = QIcon()

    for s in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(s, s)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Rounded container background
        margin = max(1.0, s * 0.05)
        rect = QRectF(margin, margin, s - margin * 2, s - margin * 2)
        radius = s * 0.22

        bg_color = QColor("#1e1e24")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor("#383842"), max(1.0, s * 0.03)))
        painter.drawRoundedRect(rect, radius, radius)

        # 2. Node tree icon lines & circles
        # Positions relative to inner box
        cx = s * 0.5
        cy = s * 0.5

        root_x = s * 0.32
        root_y = s * 0.35

        child1_x = s * 0.68
        child1_y = s * 0.35

        child2_x = s * 0.68
        child2_y = s * 0.65

        node_r = max(2.0, s * 0.1)

        # Connective branches
        line_pen = QPen(QColor("#007acc"), max(1.5, s * 0.06))
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(line_pen)

        # Horizontal to child1
        painter.drawLine(root_x, root_y, child1_x, child1_y)

        # Vertical step down to child2
        painter.drawLine(root_x, root_y, root_x, child2_y)
        painter.drawLine(root_x, child2_y, child2_x, child2_y)

        # Draw Nodes (Circles)
        # Root node (Accent Blue)
        painter.setPen(QPen(QColor("#38bdf8"), max(1.0, s * 0.03)))
        painter.setBrush(QBrush(QColor("#0284c7")))
        painter.drawEllipse(QRectF(root_x - node_r, root_y - node_r, node_r * 2, node_r * 2))

        # Child 1 node (Greenish Emerald)
        painter.setPen(QPen(QColor("#4ade80"), max(1.0, s * 0.03)))
        painter.setBrush(QBrush(QColor("#16a34a")))
        painter.drawEllipse(QRectF(child1_x - node_r, child1_y - node_r, node_r * 2, node_r * 2))

        # Child 2 node (Amber / Gold)
        painter.setPen(QPen(QColor("#fde047"), max(1.0, s * 0.03)))
        painter.setBrush(QBrush(QColor("#ca8a04")))
        painter.drawEllipse(QRectF(child2_x - node_r, child2_y - node_r, node_r * 2, node_r * 2))

        painter.end()
        icon.addPixmap(pixmap)

    return icon
