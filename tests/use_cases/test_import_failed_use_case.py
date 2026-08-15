"""Unit tests for ImportFailedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ImportFailedUseCase


class TestImportFailedUseCase:
    """Test suite for ImportFailedUseCase."""

    def test_sets_error_message(self) -> None:
        """Test that error message is set on import failure."""
        state = ScreenState()

        next_state = ImportFailedUseCase().invoke(state, "File not found")

        assert next_state.error_message == "File not found"
        assert next_state.status_message == "Import failed."

    def test_sets_import_status_to_idle(self) -> None:
        """Test that import status is set to idle on failure."""
        state = ScreenState(import_status=JobStatus.RUNNING)

        next_state = ImportFailedUseCase().invoke(state, "Read error")

        assert next_state.import_status == JobStatus.IDLE

    def test_clears_previous_error(self) -> None:
        """Test that new error overwrites previous one."""
        state = ScreenState(error_message="Old error")

        next_state = ImportFailedUseCase().invoke(state, "New error")

        assert next_state.error_message == "New error"
