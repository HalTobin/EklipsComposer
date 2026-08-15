"""Unit tests for ProjectSavedUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ProjectSavedUseCase


class TestProjectSavedUseCase:
    """Test suite for ProjectSavedUseCase."""

    def test_stores_project_path(self) -> None:
        """Test that saved project path is stored."""
        state = ScreenState()
        project_path = Path("/tmp/project.vlt")

        next_state = ProjectSavedUseCase().invoke(state, project_path)

        assert next_state.last_project_path == project_path

    def test_sets_export_status_idle(self) -> None:
        """Test that export status is set to idle."""
        state = ScreenState(export_status=JobStatus.RUNNING)

        next_state = ProjectSavedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.export_status is None

    def test_sets_progress_complete(self) -> None:
        """Test that progress is set to 100%."""
        state = ScreenState(progress=0.3)

        next_state = ProjectSavedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.progress == 1.0

    def test_clears_error_message(self) -> None:
        """Test that error message is cleared on successful save."""
        state = ScreenState(error_message="Save failed")

        next_state = ProjectSavedUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.error_message is None
