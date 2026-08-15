"""Unit tests for OpenProjectUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import OpenProjectUseCase


class TestOpenProjectUseCase:
    """Test suite for OpenProjectUseCase."""

    def test_initiates_open_job(self) -> None:
        """Test that import status is set to running."""
        state = ScreenState(import_status=None)

        next_state = OpenProjectUseCase().invoke(state, Path("/tmp/project.vlt"))

        assert next_state.import_status == JobStatus.RUNNING

    def test_sets_blocking_job_path(self) -> None:
        """Test that blocking job path is set."""
        state = ScreenState(blocking_job_path=None)
        project_path = Path("/tmp/project.vlt")

        next_state = OpenProjectUseCase().invoke(state, project_path)

        assert next_state.blocking_job_path == project_path

    def test_sets_status_message(self) -> None:
        """Test that status message is set."""
        state = ScreenState()

        next_state = OpenProjectUseCase().invoke(state, Path("/tmp/proj.vlt"))

        assert next_state.status_message is not None
        assert "open" in next_state.status_message.lower()
