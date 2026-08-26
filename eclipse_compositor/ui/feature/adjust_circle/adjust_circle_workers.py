"""Background workers for the adjust circle feature."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from eclipse_compositor.cv.detection import DiscDetection, find_disc_center
from eclipse_compositor.cv.loading import load_image_bgr

logger = logging.getLogger(__name__)


class AdjustCircleSignals(QObject):
    load_finished = Signal(object, object)  # np.ndarray, DiscDetection | None
    detect_finished = Signal(object)  # DiscDetection | None
    failed = Signal(str)


class AdjustCircleLoadWorker(QRunnable):
    """Worker that loads a single image and runs an initial detection."""

    def __init__(self, path: Path, threshold: int, signals: AdjustCircleSignals) -> None:
        super().__init__()
        self.path = path
        self.threshold = threshold
        self.signals = signals
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            image = load_image_bgr(self.path)
            detection = find_disc_center(image, threshold=self.threshold)
            self.signals.load_finished.emit(image, detection)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Adjust circle load failed")
            try:
                self.signals.failed.emit(str(exc))
            except RuntimeError:
                pass


class AdjustCircleDetectWorker(QRunnable):
    """Worker that detects a disc from an in-memory image."""

    def __init__(self, image: np.ndarray, threshold: int, signals: AdjustCircleSignals) -> None:
        super().__init__()
        self.image = image
        self.threshold = threshold
        self.signals = signals
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            detection = find_disc_center(self.image, threshold=self.threshold)
            self.signals.detect_finished.emit(detection)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Adjust circle detect failed")
            try:
                self.signals.failed.emit(str(exc))
            except RuntimeError:
                pass
