"""Confirmation dialog shown before extracting frames from a video."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QListWidget,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.video import VideoProbe, stepped_frame_count
from eclipse_compositor.ui.theme import HintLabel, Section, SPACE


class VideoImportDialog(QDialog):
    """Ask how many imported video frames to enable for the composite."""

    def __init__(self, probes: list[VideoProbe], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._probes = probes
        self.setWindowTitle("Import video frames")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        layout.setSpacing(SPACE.md)

        card = Section("Video source")
        summary = HintLabel(_source_text(probes))
        summary.setWordWrap(True)
        card.add_widget(summary)

        if len(probes) > 1:
            listing = QListWidget()
            listing.setMaximumHeight(140)
            for probe in probes:
                listing.addItem(f"{probe.path.name} — {_count_label(probe)}")
            card.add_widget(listing)
        layout.addWidget(card)

        options = Section("Composite")
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        self.step_spin = QSpinBox()
        self.step_spin.setMinimum(1)
        total = _known_total(probes)
        self.step_spin.setMaximum(total if total else 9999)
        self.step_spin.setValue(1)
        self.step_spin.setToolTip(
            "All frames are imported. 1 enables every frame for the composite; "
            "2 enables every second frame, and so on."
        )
        form.addRow("Frame step", self.step_spin)
        options.add_layout(form)

        self._enabled_label = HintLabel()
        options.add_widget(self._enabled_label)
        self.step_spin.valueChanged.connect(self._refresh_enabled_label)
        self._refresh_enabled_label()

        if total is not None and total >= 500:
            options.add_widget(
                HintLabel("Large imports may take a while and use extra disk space.")
            )
        layout.addWidget(options)

        buttons = QDialogButtonBox()
        import_btn = buttons.addButton("Import", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        import_btn.setDefault(True)
        import_btn.setProperty("variant", "primary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def frame_step(self) -> int:
        """Enable-every-N-th stride (``1`` = all frames enabled for output)."""
        return max(1, int(self.step_spin.value()))

    def _refresh_enabled_label(self) -> None:
        self._enabled_label.setText(_enabled_text(self._probes, self.frame_step))


def confirm_video_import(parent: QWidget | None, probes: list[VideoProbe]) -> int | None:
    """Show the confirmation dialog.

    Returns:
        The chosen frame step (``1`` enables every frame), or ``None`` if cancelled.
    """
    if not probes:
        return None
    dialog = VideoImportDialog(probes, parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.frame_step


def _known_total(probes: list[VideoProbe]) -> int | None:
    if any(probe.frame_count is None for probe in probes):
        return None
    return sum(probe.frame_count or 0 for probe in probes)


def _count_label(probe: VideoProbe) -> str:
    if probe.frame_count is None:
        return "all frames"
    noun = "frame" if probe.frame_count == 1 else "frames"
    return f"{probe.frame_count:,} {noun}"


def _source_text(probes: list[VideoProbe]) -> str:
    if len(probes) == 1:
        probe = probes[0]
        return f"This will import all {_count_label(probe)} from {probe.path.name}."
    total = _known_total(probes)
    n = len(probes)
    if total is None:
        return f"This will import all frames from {n} videos."
    noun = "frame" if total == 1 else "frames"
    return f"This will import all {total:,} {noun} from {n} videos."


def _enabled_text(probes: list[VideoProbe], step: int) -> str:
    stride = max(1, int(step))
    total = _known_total(probes)
    if stride == 1:
        if total is None:
            return "1 enables every imported frame for the composite."
        noun = "frame" if total == 1 else "frames"
        return f"1 enables all {total:,} {noun} for the composite."
    if total is None:
        return (
            f"Every {stride}th imported frame will be enabled for the composite; "
            "the rest stay in the gallery, unchecked."
        )
    enabled = stepped_frame_count(total, stride)
    noun = "frame" if enabled == 1 else "frames"
    return (
        f"{enabled:,} of {total:,} {noun} will be enabled for the composite; "
        "the rest stay in the gallery, unchecked."
    )
