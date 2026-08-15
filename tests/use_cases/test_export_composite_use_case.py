"""Unit tests for ExportCompositeUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ExportCompositeUseCase


class TestExportCompositeUseCase:
    """Test suite for ExportCompositeUseCase."""

    def test_initiates_export_job(self) -> None:
        """Test that export status is set to running when images exist."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/test.jpg")),),
            export_status=None,
        )

        next_state = ExportCompositeUseCase().invoke(
            state,
            Path("/tmp/output.png"),
        )

        assert next_state.export_status == JobStatus.RUNNING

    def test_sets_blocking_job_path(self) -> None:
        """Test that blocking job path is set when images exist."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/test.jpg")),),
            blocking_job_path=None,
        )
        output_path = Path("/tmp/output.png")

        next_state = ExportCompositeUseCase().invoke(state, output_path)

        assert next_state.blocking_job_path == output_path

    def test_returns_state_unchanged_when_no_images(self) -> None:
        """Test that export is skipped when there are no images."""
        state = ScreenState(images=(), export_status=None)

        next_state = ExportCompositeUseCase().invoke(state, Path("/tmp/out.png"))

        assert next_state.export_status is None
        assert next_state is state
