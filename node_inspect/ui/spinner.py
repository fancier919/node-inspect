"""Visual loading spinner widget for indicating background tasks."""

import math
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from node_inspect.ui.theme import COLORS


class SpinnerIcon(QWidget):
    """Circular animated spinner icon."""

    def __init__(self, size: int = 18, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._angle = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(25)  # 40 fps

    def _rotate(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def start(self):
        if not self._timer.isActive():
            self._timer.start()
            self.show()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw glowing arc
        rect = QRectF(2, 2, self._size - 4, self._size - 4)
        pen = QPen(QColor(COLORS["accent"]))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # 270 degree arc rotating
        start_angle = int(self._angle * 16)
        span_angle = int(240 * 16)
        painter.drawArc(rect, start_angle, span_angle)


class LoadingIndicator(QWidget):
    """Full loading indicator bar with animated spinner and status message."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 2, 8, 2)
        self.layout.setSpacing(8)

        self.spinner = SpinnerIcon(16, self)
        self.label = QLabel("Loading...", self)
        self.label.setStyleSheet(f"color: {COLORS['accent']}; font-weight: 500; font-size: 12px;")

        self.layout.addWidget(self.spinner)
        self.layout.addWidget(self.label)
        self.layout.addStretch()

        self.hide()

    def show_loading(self, text: str = "Loading data..."):
        self.label.setText(text)
        self.spinner.start()
        self.show()

    def hide_loading(self):
        self.spinner.stop()
        self.hide()
