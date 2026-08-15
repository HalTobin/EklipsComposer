"""Unit tests for UpdateMaskUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.use_cases import UpdateMaskUseCase


class TestUpdateMaskUseCase:
    """Test suite for UpdateMaskUseCase."""

    def test_enables_mask(self) -> None:
        """Test enabling the mask."""
        state = ScreenState(mask_enabled=False)

        next_state = UpdateMaskUseCase().invoke(state, enabled=True)

        assert next_state.mask_enabled is True

    def test_disables_mask(self) -> None:
        """Test disabling the mask."""
        state = ScreenState(mask_enabled=True)

        next_state = UpdateMaskUseCase().invoke(state, enabled=False)

        assert next_state.mask_enabled is False

    def test_updates_mask_size(self) -> None:
        """Test updating mask size."""
        state = ScreenState(mask_size=0.9)

        next_state = UpdateMaskUseCase().invoke(state, size=1.0)

        assert next_state.mask_size == 1.0

    def test_clamps_mask_size_to_maximum(self) -> None:
        """Test clamping mask size to maximum (1.50)."""
        state = ScreenState(mask_size=0.9)

        next_state = UpdateMaskUseCase().invoke(state, size=2.0)

        assert next_state.mask_size == 1.50

    def test_clamps_mask_size_to_minimum(self) -> None:
        """Test clamping mask size to minimum (0.0)."""
        state = ScreenState(mask_size=0.9)

        next_state = UpdateMaskUseCase().invoke(state, size=-1.0)

        assert next_state.mask_size == 0.0

    def test_updates_mask_feather(self) -> None:
        """Test updating mask feather."""
        state = ScreenState(mask_feather=0.2)

        next_state = UpdateMaskUseCase().invoke(state, feather=0.3)

        assert next_state.mask_feather == 0.3

    def test_clamps_mask_feather_to_maximum(self) -> None:
        """Test clamping mask feather to maximum (0.80)."""
        state = ScreenState(mask_feather=0.2)

        next_state = UpdateMaskUseCase().invoke(state, feather=1.0)

        assert next_state.mask_feather == 0.80

    def test_clamps_mask_feather_to_minimum(self) -> None:
        """Test clamping mask feather to minimum (0.0)."""
        state = ScreenState(mask_feather=0.2)

        next_state = UpdateMaskUseCase().invoke(state, feather=-0.5)

        assert next_state.mask_feather == 0.0

    def test_updates_both_mask_params(self) -> None:
        """Test updating both mask size and feather."""
        state = ScreenState(mask_size=0.9, mask_feather=0.2)

        next_state = UpdateMaskUseCase().invoke(
            state,
            size=1.0,
            feather=0.4,
        )

        assert next_state.mask_size == 1.0
        assert next_state.mask_feather == 0.4
