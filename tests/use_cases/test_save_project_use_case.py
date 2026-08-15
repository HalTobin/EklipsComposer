"""Unit tests for SaveProjectUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import SaveProjectUseCase


class TestSaveProjectUseCase:
    """Test suite for SaveProjectUseCase."""

    def test_initiates_save_job(self) -> None:
        """Test that export status is set to running when images exist."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/test.jpg")),),
            export_status=None,
        )

        next_state = SaveProjectUseCase().invoke(state, Path("/tmp/project.vlt"))

        assert next_state.export_status == JobStatus.RUNNING

    def test_sets_blocking_job_path(self) -> None:
        """Test that blocking job path is set when images exist."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/test.jpg")),),
            blocking_job_path=None,
        )
        project_path = Path("/tmp/project.vlt")

        next_state = SaveProjectUseCase().invoke(state, project_path)

        assert next_state.blocking_job_path == project_path

    def test_returns_state_unchanged_when_no_images(self) -> None:
        """Test that save is skipped when there are no images."""
        state = ScreenState(images=(), export_status=None)

        next_state = SaveProjectUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.export_status is None
        assert next_state is state
