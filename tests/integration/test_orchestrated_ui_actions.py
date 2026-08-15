import os
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.ui.actions import (
    CancelJob,
    ClearImages,
    ExportComposite,
    LoadImages,
    OpenProject,
    ReorderImages,
    RemoveImage,
    RequestPreview,
    SaveProject,
    SelectImage,
    SelectSidebarTab,
    ToggleImage,
    UpdateArcAngle,
    UpdateBrightness,
    UpdateContrast,
    UpdateCropSize,
    UpdateDirection,
    UpdateGamma,
    UpdateGridColumns,
    UpdateGridRows,
    UpdateLayout,
    UpdateMarginGlobal,
    UpdateMarginLinked,
    UpdateMarginX,
    UpdateMarginY,
    UpdateMaskEnabled,
    UpdateMaskFeather,
    UpdateMaskSize,
    UpdateSaturation,
    UpdateSpacing,
    UpdateTemperature,
    UpdateThreshold,
    UpdateZoom,
    ResetColorimetry,
)
from eclipse_compositor.ui.state import (
    DEFAULT_MARGIN,
    BlockingJob,
    ImageItem,
    JobStatus,
    SidebarTab,
)
from eclipse_compositor.ui.viewmodel import ScreenViewModel


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app


class _BaseScreenActionTests:
    @pytest.fixture(autouse=True)
    def setup_vm(self, qt_app: QApplication) -> None:
        self.vm = ScreenViewModel()
        self.vm._state = replace(
            self.vm.state,
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
                ImageItem(path=Path("/tmp/third.jpg"), enabled=True),
            ),
            selected_index=1,
            proxy_ready=True,
            preview_bgr=np.zeros((64, 64, 3), dtype=np.uint8),
            native_max_resolution=2400,
        )


class TestGalleryActionOrchestration(_BaseScreenActionTests):
    def test_load_images_action_starts_import_flow(self) -> None:
        paths = (Path("/tmp/alpha.jpg"), Path("/tmp/beta.jpg"))

        self.vm.dispatch(LoadImages(paths))

        assert self.vm.state.import_status is JobStatus.RUNNING
        assert self.vm.state.status_message == "Importing…"

    def test_gallery_actions_keep_selection_and_state_in_sync(self) -> None:
        self.vm.dispatch(ToggleImage(1, False))
        assert self.vm.state.images[1].enabled is False

        self.vm.dispatch(SelectImage(0))
        assert self.vm.state.selected_index == 0

        self.vm.dispatch(RemoveImage((0,)))
        assert [item.path for item in self.vm.state.images] == [
            Path("/tmp/second.jpg"),
            Path("/tmp/third.jpg"),
        ]
        assert self.vm.state.selected_index == 0

        reordered = (
            ImageItem(path=Path("/tmp/third.jpg"), enabled=True),
            ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
        )
        self.vm.dispatch(ReorderImages(reordered))
        assert [item.path for item in self.vm.state.images] == [
            Path("/tmp/third.jpg"),
            Path("/tmp/second.jpg"),
        ]

        self.vm.dispatch(ClearImages())
        assert self.vm.state.images == ()
        assert self.vm.state.selected_index is None
        assert self.vm.state.proxy_ready is False


class TestLayoutAndPreviewActionOrchestration(_BaseScreenActionTests):
    def test_layout_and_preview_actions_update_composite_state(self) -> None:
        states = []
        self.vm.state_changed.connect(lambda state: states.append(state))

        self.vm.dispatch(UpdateCropSize(1600))
        self.vm.dispatch(UpdateSpacing(-0.35))
        self.vm.dispatch(UpdateLayout(LayoutType.LINEAR))
        self.vm.dispatch(UpdateArcAngle(75.0))
        self.vm.dispatch(UpdateDirection(LayoutDirection.VERTICAL))
        self.vm.dispatch(UpdateThreshold(220))
        self.vm.dispatch(UpdateGridColumns(4))
        self.vm.dispatch(UpdateGridRows(3))
        self.vm.dispatch(UpdateZoom(1.75))
        self.vm.dispatch(SelectSidebarTab(SidebarTab.CANVAS))
        self.vm.dispatch(RequestPreview())

        assert self.vm.state.crop_size == 1600
        assert self.vm.state.spacing == -0.35
        assert self.vm.state.layout is LayoutType.LINEAR
        assert self.vm.state.arc_angle == 75.0
        assert self.vm.state.direction is LayoutDirection.VERTICAL
        assert self.vm.state.threshold == 220
        assert self.vm.state.grid_columns == 4
        assert self.vm.state.grid_rows == 3
        assert self.vm.state.zoom == 1.75
        assert self.vm.state.sidebar_tab is SidebarTab.CANVAS
        assert states and states[-1].layout is LayoutType.LINEAR


class TestColorimetryAndMaskActionOrchestration(_BaseScreenActionTests):
    def test_colorimetry_and_mask_actions_are_applied_and_reset(self) -> None:
        self.vm.dispatch(UpdateContrast(1.4))
        self.vm.dispatch(UpdateSaturation(1.8))
        self.vm.dispatch(UpdateBrightness(20.0))
        self.vm.dispatch(UpdateGamma(1.3))
        self.vm.dispatch(UpdateTemperature(-15.0))
        self.vm.dispatch(UpdateMaskEnabled(True))
        self.vm.dispatch(UpdateMaskSize(0.75))
        self.vm.dispatch(UpdateMaskFeather(0.38))
        self.vm.dispatch(UpdateMarginLinked(False))
        self.vm.dispatch(UpdateMarginX(120))
        self.vm.dispatch(UpdateMarginY(200))
        self.vm.dispatch(UpdateMarginGlobal(140))

        assert self.vm.state.contrast == 1.4
        assert self.vm.state.saturation == 1.8
        assert self.vm.state.brightness == 20.0
        assert self.vm.state.gamma == 1.3
        assert self.vm.state.temperature == -15.0
        assert self.vm.state.mask_enabled is True
        assert self.vm.state.mask_size == 0.75
        assert self.vm.state.mask_feather == 0.38
        assert self.vm.state.margin_linked is True
        assert self.vm.state.margin_x == 140
        assert self.vm.state.margin_y == 140

        self.vm.dispatch(ResetColorimetry())
        assert self.vm.state.contrast == 1.0
        assert self.vm.state.saturation == 1.0
        assert self.vm.state.brightness == 0.0
        assert self.vm.state.gamma == 1.0
        assert self.vm.state.temperature == 0.0

        self.vm.dispatch(UpdateMarginLinked(False))
        self.vm.dispatch(UpdateMarginX(75))
        self.vm.dispatch(UpdateMarginY(125))
        assert self.vm.state.margin_linked is False
        assert self.vm.state.margin_x == 75
        assert self.vm.state.margin_y == 125


class TestProjectAndJobActionOrchestration(_BaseScreenActionTests):
    def test_export_and_project_actions_fail_gracefully_without_frames(self) -> None:
        self.vm._state = replace(self.vm.state, images=(), proxy_ready=False)

        self.vm.dispatch(ExportComposite(Path("/tmp/exported.jpg")))
        assert self.vm.state.error_message == "No frames enabled for export."
        assert self.vm.state.export_status is JobStatus.IDLE

        self.vm.dispatch(SaveProject(Path("/tmp/project.vlt")))
        assert self.vm.state.error_message == "No frames to save."
        assert self.vm.state.status_message == "Save failed."

        self.vm.dispatch(OpenProject(Path("/tmp/project.vlt")))
        assert self.vm.state.import_status is JobStatus.RUNNING

    def test_cancel_job_action_sets_cancellation_state(self) -> None:
        self.vm._state = replace(
            self.vm.state,
            blocking_job=BlockingJob.SAVE,
            blocking_job_path=Path("/tmp/project.vlt"),
            blocking_job_cancelling=False,
        )
        self.vm._job_cancel = self.vm._job_cancel or __import__("threading").Event()

        self.vm.dispatch(CancelJob())

        assert self.vm.state.blocking_job_cancelling is True
        assert self.vm.state.status_message == "Cancelling…"

    def test_request_preview_without_images_reports_clear_error(self) -> None:
        self.vm._state = replace(self.vm.state, images=(), proxy_ready=False)

        self.vm.dispatch(RequestPreview())

        assert self.vm.state.status_message == "Import photos before previewing."
