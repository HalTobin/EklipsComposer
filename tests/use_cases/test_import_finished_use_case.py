"""Unit tests for ImportFinishedUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import ImportFinishedUseCase


class TestImportFinishedUseCase:
    """Test suite for ImportFinishedUseCase."""

    def test_updates_proxy_generation(self) -> None:
        """Test that proxy generation is updated."""
        state = ScreenState()

        next_state = ImportFinishedUseCase().invoke(state, (), 7, 2000)

        assert next_state._proxy_generation == 7

    def test_records_full_shapes(self) -> None:
        """Test that native max resolution is recorded."""
        state = ScreenState()

        next_state = ImportFinishedUseCase().invoke(
            state,
            (),
            5,
            2000,
        )

        assert next_state.native_max_resolution == 2000

    def test_sets_import_status_none(self) -> None:
        """Test that import status is set to None (idle)."""
        state = ScreenState(import_status=JobStatus.RUNNING)

        next_state = ImportFinishedUseCase().invoke(state, (), 1, 1024)

        assert next_state.import_status is None

    def test_sets_proxy_ready(self) -> None:
        """Test that proxy_ready is set to True."""
        state = ScreenState(proxy_ready=False)

        next_state = ImportFinishedUseCase().invoke(state, (), 1, 1024)

        assert next_state.proxy_ready is True
