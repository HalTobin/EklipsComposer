"""Full-window lock overlay for save, load, and export."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.state import BlockingJob, ScreenState
from eclipse_compositor.ui.theme import TYPE, ActionButton, CaptionLabel, HintLabel

_TITLES: dict[BlockingJob, str] = {
    BlockingJob.SAVE: "Saving",
    BlockingJob.OPEN: "Loading",
    BlockingJob.EXPORT: "Exporting",
}

_CARD_WIDTH = 360
_PERCENT_SAMPLE = "100 %"


class JobOverlay(QWidget):
    """Dimmed lock overlay with title, file name, progress, and Cancel."""

    cancel_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("jobOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addStretch(1)

        card = QFrame()
        card.setObjectName("jobCard")
        card.setFixedWidth(_CARD_WIDTH)
        inner_width = _CARD_WIDTH - 48
        col = QVBoxLayout(card)
        col.setContentsMargins(24, 24, 24, 20)
        col.setSpacing(10)

        self._title = QLabel()
        self._title.setObjectName("jobTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setMaximumWidth(inner_width)
        self._file = HintLabel()
        self._file.setObjectName("jobFile")
        self._file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._file.setWordWrap(True)
        self._file.setMaximumWidth(inner_width)
        self._progress = QProgressBar()
        self._progress.setRange(0, 1000)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._percent = QLabel(_PERCENT_SAMPLE)
        self._percent.setObjectName("jobPercent")
        self._percent.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        mono.setPixelSize(TYPE.ui)
        mono.setFixedPitch(True)
        self._percent.setFont(mono)
        self._percent.setFixedWidth(
            self._percent.fontMetrics().horizontalAdvance(_PERCENT_SAMPLE)
        )
        bar_row = QHBoxLayout()
        bar_row.setContentsMargins(0, 0, 0, 0)
        bar_row.setSpacing(8)
        bar_row.addWidget(self._progress, stretch=1)
        bar_row.addWidget(self._percent)
        self._status = CaptionLabel()
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setMaximumWidth(inner_width)
        self._cancel = ActionButton("Cancel", variant="ghost")
        self._cancel.clicked.connect(self.cancel_clicked.emit)

        col.addWidget(self._title)
        col.addWidget(self._file)
        col.addLayout(bar_row)
        col.addWidget(self._status)
        col.addWidget(self._cancel, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch(1)

    def render(self, state: ScreenState) -> None:
        """Show or hide the overlay to match *state*."""
        job = state.blocking_job
        if job is None:
            self._cancel.setShortcut(QKeySequence())
            self.hide()
            return
        title = "Cancelling" if state.blocking_job_cancelling else _TITLES[job]
        path = state.blocking_job_path
        filename = path.name if path is not None else ""
        self._title.setText(title)
        self._file.setText(filename)
        self._file.setToolTip(str(path) if path is not None else "")
        self._file.setVisible(bool(filename))
        fraction = max(0.0, min(1.0, float(state.progress)))
        percent = int(round(fraction * 100))
        self._progress.setValue(int(round(fraction * 1000)))
        self._percent.setText(f"{percent:3d} %")
        self._status.setText(state.status_message)
        self._status.setVisible(bool(state.status_message.strip()))
        self._cancel.setEnabled(not state.blocking_job_cancelling)
        self._cancel.setShortcut(QKeySequence.StandardKey.Cancel)
        appeared = not self.isVisible()
        self.show()
        self.raise_()
        if appeared and not state.blocking_job_cancelling:
            self._cancel.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
