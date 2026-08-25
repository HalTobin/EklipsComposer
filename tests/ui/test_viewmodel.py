"""Unit tests for ScreenViewModel orchestration (dispatch → use cases → state)."""

import os
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.actions import (
    CancelJob,
    ExportComposite,
    ExportFailed,
    OpenProject,
    ResetColorimetry,
    SaveProject,
    SaveProjectFailed,
    SelectImage,
    SelectSidebarTab,
    UpdateBrightness,
    UpdateProjectGalleryHidden,
)
from eclipse_compositor.ui.state import (
    BlockingJob,
    CanvasItem,
    ImageItem,
    JobStatus,
    MediaItem,
    ProjectSortMode,
    SidebarTab,
)
from eclipse_compositor.ui.view import ScreenView
from eclipse_compositor.ui.viewmodel import ScreenViewModel


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def vm(qt_app: QApplication) -> ScreenViewModel:
    view_model = ScreenViewModel()
    view_model._state = replace(
        view_model.state,
        images=(
            ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
            ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
        ),
        selected_index=0,
        proxy_ready=True,
        preview_bgr=np.zeros((4, 4, 3), dtype=np.uint8),
    )
    return view_model


class TestSelectImage:
    def test_selects_valid_index_and_attaches_proxy(self, vm: ScreenViewModel) -> None:
        proxy = np.ones((2, 2, 3), dtype=np.uint8)
        vm._assets.proxy_cache[Path("/tmp/second.jpg")] = proxy

        vm.dispatch(SelectImage(1))

        assert vm.state.selected_index == 1
        assert vm.state.selected_preview_bgr is proxy

    def test_out_of_range_index_clears_selection(self, vm: ScreenViewModel) -> None:
        vm.dispatch(SelectImage(99))

        assert vm.state.selected_index is None
        assert vm.state.selected_preview_bgr is None


class TestSelectSidebarTab:
    def test_switches_tab(self, vm: ScreenViewModel) -> None:
        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(SelectSidebarTab(SidebarTab.MASK))

        assert vm.state.sidebar_tab == SidebarTab.MASK
        assert len(received) == 1

    def test_reselecting_same_tab_is_a_noop(self, vm: ScreenViewModel) -> None:
        vm.dispatch(SelectSidebarTab(SidebarTab.COMPOSITE))
        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(SelectSidebarTab(SidebarTab.COMPOSITE))

        assert received == []


class TestProjectGalleryVisibility:
    def test_updates_visibility_and_ignores_the_same_value(self, vm: ScreenViewModel) -> None:
        vm.dispatch(UpdateProjectGalleryHidden(True))

        assert vm.state.project_gallery_hidden is True

        received: list = []
        vm.state_changed.connect(received.append)
        vm.dispatch(UpdateProjectGalleryHidden(True))

        assert received == []


class TestResetColorimetry:
    def test_noop_when_already_default(self, vm: ScreenViewModel) -> None:
        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(ResetColorimetry())

        assert received == []

    def test_resets_adjusted_values(self, vm: ScreenViewModel) -> None:
        vm.dispatch(UpdateBrightness(42.0))
        assert vm.state.brightness == 42.0

        vm.dispatch(ResetColorimetry())

        assert vm.state.brightness == 0.0


class TestCancelJob:
    def test_noop_without_active_blocking_job(self, vm: ScreenViewModel) -> None:
        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(CancelJob())

        assert received == []

    def test_cancels_active_export_job(self, vm: ScreenViewModel) -> None:
        vm.dispatch(ExportComposite(Path("/tmp/out.tiff")))
        assert vm.state.blocking_job is BlockingJob.EXPORT
        assert vm._job_cancel is not None

        vm.dispatch(CancelJob())

        assert vm.state.blocking_job_cancelling is True
        assert vm.state.status_message == "Cancelling…"
        assert vm._job_cancel.is_set()

    def test_second_cancel_request_is_a_noop(self, vm: ScreenViewModel) -> None:
        vm.dispatch(ExportComposite(Path("/tmp/out.tiff")))
        vm.dispatch(CancelJob())
        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(CancelJob())

        assert received == []


class TestExportComposite:
    def test_starts_export_job_with_blocking_overlay(self, vm: ScreenViewModel) -> None:
        vm.dispatch(ExportComposite(Path("/tmp/out.tiff")))

        assert vm.state.export_status is JobStatus.RUNNING
        assert vm.state.blocking_job is BlockingJob.EXPORT
        assert vm.state.blocking_job_path == Path("/tmp/out.tiff")
        assert vm.state.blocking_job_cancelling is False
        assert vm.state.status_message == "Exporting…"

    def test_no_enabled_frames_fails_without_starting_job(self, vm: ScreenViewModel) -> None:
        vm._state = replace(
            vm.state,
            images=tuple(replace(item, enabled=False) for item in vm.state.images),
        )

        vm.dispatch(ExportComposite(Path("/tmp/out.tiff")))

        assert vm.state.blocking_job is None
        assert vm.state.export_status is JobStatus.IDLE
        assert vm.state.error_message == "No frames enabled for export."


class TestSaveProject:
    def test_starts_save_job_with_blocking_overlay(self, vm: ScreenViewModel) -> None:
        vm.dispatch(SaveProject(Path("/tmp/proj.eklips")))

        assert vm.state.export_status is JobStatus.RUNNING
        assert vm.state.blocking_job is BlockingJob.SAVE
        assert vm.state.blocking_job_path == Path("/tmp/proj.eklips")
        assert vm.state.blocking_job_cancelling is False

    def test_no_images_fails_without_starting_job(self, vm: ScreenViewModel) -> None:
        vm._state = replace(vm.state, images=())

        vm.dispatch(SaveProject(Path("/tmp/proj.eklips")))

        assert vm.state.blocking_job is None
        assert vm.state.error_message == "No frames to save."


class TestOpenProject:
    def test_starts_open_job_with_blocking_overlay(self, vm: ScreenViewModel) -> None:
        vm.dispatch(OpenProject(Path("/tmp/proj.eklips")))

        assert vm.state.import_status is JobStatus.RUNNING
        assert vm.state.blocking_job is BlockingJob.OPEN
        assert vm.state.blocking_job_path == Path("/tmp/proj.eklips")
        assert vm.state.blocking_job_cancelling is False


class TestIoBusyGuards:
    def test_export_is_ignored_while_import_running(self, vm: ScreenViewModel) -> None:
        vm._state = replace(vm.state, import_status=JobStatus.RUNNING)

        vm.dispatch(ExportComposite(Path("/tmp/out.tiff")))

        assert vm.state.blocking_job is None

    def test_open_project_is_ignored_while_export_running(self, vm: ScreenViewModel) -> None:
        vm._state = replace(vm.state, export_status=JobStatus.RUNNING)

        vm.dispatch(OpenProject(Path("/tmp/proj.eklips")))

        assert vm.state.blocking_job is None


class TestUnknownAction:
    def test_unhandled_action_does_not_emit_or_raise(self, vm: ScreenViewModel) -> None:
        class _Unknown:
            pass

        received: list = []
        vm.state_changed.connect(received.append)

        vm.dispatch(_Unknown())  # type: ignore[arg-type]

        assert received == []
