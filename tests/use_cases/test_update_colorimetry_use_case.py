"""Unit tests for UpdateColorimetryUseCase."""

import pytest

from eclipse_compositor.ui.state import (
    ScreenState,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CONTRAST,
    DEFAULT_GAMMA,
    DEFAULT_SATURATION,
    DEFAULT_TEMPERATURE,
)
from eclipse_compositor.ui.use_cases import UpdateColorimetryUseCase


class TestUpdateColorimetryUseCase:
    """Test suite for UpdateColorimetryUseCase."""

    def test_updates_brightness(self) -> None:
        """Test updating brightness parameter."""
        state = ScreenState(brightness=0.0)

        next_state = UpdateColorimetryUseCase().invoke(state, brightness=50.0)

        assert next_state.brightness == 50.0

    def test_clamps_brightness(self) -> None:
        """Test clamping brightness to valid range [-100, 100]."""
        state = ScreenState(brightness=0.0)

        next_state = UpdateColorimetryUseCase().invoke(state, brightness=200.0)

        assert next_state.brightness == 100.0

    def test_updates_contrast(self) -> None:
        """Test updating contrast parameter."""
        state = ScreenState(contrast=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, contrast=0.8)

        assert next_state.contrast == 0.8

    def test_clamps_contrast(self) -> None:
        """Test clamping contrast to valid range [0.5, 2.0]."""
        state = ScreenState(contrast=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, contrast=3.0)

        assert next_state.contrast == 2.0

    def test_updates_saturation(self) -> None:
        """Test updating saturation parameter."""
        state = ScreenState(saturation=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, saturation=1.2)

        assert next_state.saturation == 1.2

    def test_clamps_saturation(self) -> None:
        """Test clamping saturation to valid range [0.0, 2.0]."""
        state = ScreenState(saturation=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, saturation=3.0)

        assert next_state.saturation == 2.0

    def test_updates_gamma(self) -> None:
        """Test updating gamma parameter."""
        state = ScreenState(gamma=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, gamma=0.9)

        assert next_state.gamma == 0.9

    def test_clamps_gamma(self) -> None:
        """Test clamping gamma to valid range [0.5, 2.0]."""
        state = ScreenState(gamma=1.0)

        next_state = UpdateColorimetryUseCase().invoke(state, gamma=5.0)

        assert next_state.gamma == 2.0

    def test_updates_temperature(self) -> None:
        """Test updating color temperature."""
        state = ScreenState(temperature=0.0)

        next_state = UpdateColorimetryUseCase().invoke(state, temperature=-50.0)

        assert next_state.temperature == -50.0

    def test_clamps_temperature(self) -> None:
        """Test clamping temperature to valid range [-100, 100]."""
        state = ScreenState(temperature=0.0)

        next_state = UpdateColorimetryUseCase().invoke(state, temperature=500.0)

        assert next_state.temperature == 100.0

    def test_reset_restores_defaults(self) -> None:
        """Test that reset=True restores all parameters to defaults."""
        state = ScreenState(
            brightness=50.0,
            contrast=0.5,
            saturation=2.0,
            gamma=0.5,
            temperature=100.0,
        )

        next_state = UpdateColorimetryUseCase().invoke(state, reset=True)

        assert next_state.brightness == DEFAULT_BRIGHTNESS
        assert next_state.contrast == DEFAULT_CONTRAST
        assert next_state.saturation == DEFAULT_SATURATION
        assert next_state.gamma == DEFAULT_GAMMA
        assert next_state.temperature == DEFAULT_TEMPERATURE

    def test_updates_multiple_params(self) -> None:
        """Test updating multiple colorimetry parameters at once."""
        state = ScreenState(
            brightness=0.0,
            contrast=1.0,
            saturation=1.0,
        )

        next_state = UpdateColorimetryUseCase().invoke(
            state,
            brightness=20.0,
            contrast=0.9,
            saturation=1.05,
        )

        assert next_state.brightness == 20.0
        assert next_state.contrast == 0.9
        assert next_state.saturation == 1.05
