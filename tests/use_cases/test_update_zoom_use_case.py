"""Unit tests for UpdateZoomUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.use_cases import UpdateZoomUseCase


class TestUpdateZoomUseCase:
    """Test suite for UpdateZoomUseCase."""

    def test_updates_zoom_level(self) -> None:
        """Test updating zoom level."""
        state = ScreenState(zoom=1.0)

        next_state = UpdateZoomUseCase().invoke(state, 1.5)

        assert next_state.zoom == 1.5

    def test_sets_zoom_to_fit(self) -> None:
        """Test setting zoom to fit-to-window."""
        state = ScreenState(zoom=2.0)

        next_state = UpdateZoomUseCase().invoke(state, 0.8)

        assert next_state.zoom == 0.8

    def test_clamps_zoom_to_minimum(self) -> None:
        """Test clamping to minimum zoom (0.01)."""
        state = ScreenState(zoom=1.0)

        next_state = UpdateZoomUseCase().invoke(state, 0.001)

        assert next_state.zoom == 0.01

    def test_clamps_zoom_to_maximum(self) -> None:
        """Test clamping to maximum zoom (8.0)."""
        state = ScreenState(zoom=1.0)

        next_state = UpdateZoomUseCase().invoke(state, 10.0)

        assert next_state.zoom == 8.0

    def test_returns_unchanged_state_when_zoom_same(self) -> None:
        """Test that state is not replaced if zoom is nearly identical."""
        state = ScreenState(zoom=1.0)

        next_state = UpdateZoomUseCase().invoke(state, 1.0)

        assert next_state is state
