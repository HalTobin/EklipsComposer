"""Unit tests for ExportFinishedUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ExportFinishedUseCase


class TestExportFinishedUseCase:
    """Test suite for ExportFinishedUseCase."""

    def test_stores_output_path(self) -> None:
        """Test that export output path is stored."""
        state = ScreenState()
        output = Path("/tmp/output.png")

        next_state = ExportFinishedUseCase().invoke(state, output)

        assert next_state.last_export_path == output

    def test_sets_export_status_idle(self) -> None:
        """Test that export status is set to idle."""
        state = ScreenState(export_status=JobStatus.RUNNING)

        next_state = ExportFinishedUseCase().invoke(state, Path("/tmp/out.png"))

        assert next_state.export_status is None

    def test_sets_progress_complete(self) -> None:
        """Test that progress is set to 100%."""
        state = ScreenState(progress=0.5)

        next_state = ExportFinishedUseCase().invoke(state, Path("/tmp/out.png"))

        assert next_state.progress == 1.0

    def test_clears_error_message(self) -> None:
        """Test that error message is cleared on successful export."""
        state = ScreenState(error_message="Export failed")

        next_state = ExportFinishedUseCase().invoke(state, Path("/tmp/out.png"))

        assert next_state.error_message is None
