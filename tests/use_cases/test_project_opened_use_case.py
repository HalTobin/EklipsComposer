"""Unit tests for ProjectOpenedUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ProjectOpenedUseCase


class TestProjectOpenedUseCase:
    """Test suite for ProjectOpenedUseCase."""

    def test_stores_project_path(self) -> None:
        """Test that opened project path is stored."""
        state = ScreenState()
        project_path = Path("/tmp/project.vlt")

        next_state = ProjectOpenedUseCase().invoke(state, project_path)

        assert next_state.last_project_path == project_path

    def test_sets_import_status_idle(self) -> None:
        """Test that import status is set to idle."""
        state = ScreenState(import_status=JobStatus.RUNNING)

        next_state = ProjectOpenedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.import_status is None

    def test_sets_progress_complete(self) -> None:
        """Test that progress is set to 100%."""
        state = ScreenState(progress=0.7)

        next_state = ProjectOpenedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.progress == 1.0

    def test_clears_error_message(self) -> None:
        """Test that error message is cleared on successful open."""
        state = ScreenState(error_message="Open failed")

        next_state = ProjectOpenedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.error_message is None
