"""Unit tests for UpdateCanvasUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, MIN_MARGIN, MAX_MARGIN
from eclipse_compositor.ui.use_cases import UpdateCanvasUseCase


class TestUpdateCanvasUseCase:
    """Test suite for UpdateCanvasUseCase."""

    def test_updates_margin_linked(self) -> None:
        """Test updating the margin linked flag."""
        state = ScreenState(margin_linked=False)

        next_state = UpdateCanvasUseCase().invoke(state, margin_linked=True)

        assert next_state.margin_linked is True

    def test_updates_margin_x(self) -> None:
        """Test updating X margin."""
        state = ScreenState(margin_x=10)

        next_state = UpdateCanvasUseCase().invoke(state, margin_x=15)

        assert next_state.margin_x == 15

    def test_updates_margin_y(self) -> None:
        """Test updating Y margin."""
        state = ScreenState(margin_y=10)

        next_state = UpdateCanvasUseCase().invoke(state, margin_y=25)

        assert next_state.margin_y == 25

    def test_updates_margin_global_sets_both_and_linked(self) -> None:
        """Test that updating global margin sets both X/Y and marks linked."""
        state = ScreenState(margin_x=10, margin_y=10, margin_linked=False)

        next_state = UpdateCanvasUseCase().invoke(state, margin_global=20)

        assert next_state.margin_x == 20
        assert next_state.margin_y == 20
        assert next_state.margin_linked is True

    def test_clamps_margins_to_min(self) -> None:
        """Test clamping margins to minimum."""
        state = ScreenState(margin_x=10)

        next_state = UpdateCanvasUseCase().invoke(state, margin_x=-10000)

        assert next_state.margin_x == MIN_MARGIN

    def test_clamps_margins_to_max(self) -> None:
        """Test clamping margins to maximum."""
        state = ScreenState(margin_x=10)

        next_state = UpdateCanvasUseCase().invoke(state, margin_x=10000)

        assert next_state.margin_x == MAX_MARGIN

    def test_updates_multiple_params(self) -> None:
        """Test updating multiple margin parameters at once."""
        state = ScreenState(margin_linked=False, margin_x=10, margin_y=10)

        next_state = UpdateCanvasUseCase().invoke(
            state,
            margin_linked=True,
            margin_x=20,
            margin_y=30,
        )

        assert next_state.margin_linked is True
        assert next_state.margin_x == 20
        assert next_state.margin_y == 30
