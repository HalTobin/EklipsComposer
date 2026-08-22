"""ViewModel for the adjust circle feature dialog."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, Signal

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.actions import (
    AdjustCircleAction,
    ApplyAdjustment,
    AutoDetect,
    DetectCircleResult,
    LoadAdjustCircleImageResult,
    OpenAdjustCircle,
    ToggleCircleVisibility,
    UpdateAdjustCircleThreshold,
)
from eclipse_compositor.ui.feature.adjust_circle.state import AdjustCircleState
from eclipse_compositor.ui.feature.adjust_circle.use_cases import AdjustCircleUseCases
from eclipse_compositor.ui.feature.adjust_circle.workers import (
    AdjustCircleDetectWorker,
    AdjustCircleLoadWorker,
    AdjustCircleSignals,
)

logger = logging.getLogger(__name__)


class AdjustCircleViewModel(QObject):
    state_changed = Signal(object)  # AdjustCircleState
    manual_detection_applied = Signal(int, object)

    def __init__(
        self,
        parent: QObject | None = None,
        use_cases: AdjustCircleUseCases | None = None,
    ) -> None:
        if isinstance(parent, AdjustCircleUseCases) and use_cases is None:
            use_cases = parent
            parent = None
        super().__init__(parent)
        self._state = AdjustCircleState()
        self._use_cases = use_cases or AdjustCircleUseCases()
        self._pool = QThreadPool.globalInstance()
        self._signals = AdjustCircleSignals(self)
        self._signals.load_finished.connect(self._on_load_finished)
        self._signals.detect_finished.connect(self._on_detect_finished)
        self._signals.failed.connect(self._on_failed)

    @property
    def state(self) -> AdjustCircleState:
        return self._state

    @property
    def use_cases(self) -> AdjustCircleUseCases:
        return self._use_cases

    def dispatch(self, action: AdjustCircleAction) -> None:
        match action:
            case OpenAdjustCircle(index=index, path=path, threshold=threshold):
                self._state = self._use_cases.load_adjust_circle.invoke(
                    self._state,
                    path,
                    index,
                    threshold,
                )
                self.state_changed.emit(self._state)
                self._pool.start(AdjustCircleLoadWorker(path, threshold, self._signals))

            case UpdateAdjustCircleThreshold(value=value):
                self._state = self._use_cases.update_adjust_circle.invoke(
                    self._state,
                    threshold=value,
                )
                self.state_changed.emit(self._state)

            case AutoDetect():
                if self._state.image_bgr is None:
                    return
                self._state = self._use_cases.update_adjust_circle.invoke(
                    self._state,
                    is_loading=True,
                    error_message=None,
                )
                self.state_changed.emit(self._state)
                self._pool.start(
                    AdjustCircleDetectWorker(
                        self._state.image_bgr,
                        self._state.threshold,
                        self._signals,
                    )
                )

            case ToggleCircleVisibility(visible=visible):
                self._state = self._use_cases.update_adjust_circle.invoke(
                    self._state,
                    show_circle=visible,
                )
                self.state_changed.emit(self._state)

            case DetectCircleResult(detection=detection):
                self._state = self._use_cases.update_adjust_circle.invoke(
                    self._state,
                    detection=detection,
                    is_loading=False,
                    is_ready=True,
                )
                self.state_changed.emit(self._state)

            case LoadAdjustCircleImageResult(image=image, detection=detection):
                self._state = self._use_cases.update_adjust_circle.invoke(
                    self._state,
                    image_bgr=image,
                    detection=detection,
                    is_loading=False,
                    is_ready=True,
                )
                self.state_changed.emit(self._state)

            case ApplyAdjustment():
                if self._state.image_index is None or self._state.detection is None:
                    return
                self._state = self._use_cases.apply_adjust_circle.invoke(
                    self._state,
                    self._state.image_index,
                    self._state.detection,
                )
                self.state_changed.emit(self._state)
                self.manual_detection_applied.emit(self._state.image_index, self._state.detection)

            case _:
                logger.debug("Unhandled adjust circle action: %s", type(action).__name__)

    def _on_load_finished(self, image: object, detection: DiscDetection | None) -> None:
        self.dispatch(LoadAdjustCircleImageResult(image=image, detection=detection))

    def _on_detect_finished(self, detection: DiscDetection | None) -> None:
        self.dispatch(DetectCircleResult(detection=detection))

    def _on_failed(self, message: str) -> None:
        self._state = self._use_cases.update_adjust_circle.invoke(
            self._state,
            error_message=message,
            is_loading=False,
        )
        self.state_changed.emit(self._state)
