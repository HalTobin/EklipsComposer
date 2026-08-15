"""Unit tests for ToggleImageUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import ToggleImageUseCase


class TestToggleImageUseCase:
    """Test suite for ToggleImageUseCase."""

    def test_disables_enabled_image(self) -> None:
        """Test disabling an enabled image."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
            ),
        )

        next_state = ToggleImageUseCase().invoke(state, 1, False)

        assert next_state.images[0].enabled is True
        assert next_state.images[1].enabled is False

    def test_enables_disabled_image(self) -> None:
        """Test enabling a disabled image."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=False),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
            ),
        )

        next_state = ToggleImageUseCase().invoke(state, 0, True)

        assert next_state.images[0].enabled is True
        assert next_state.images[1].enabled is True

    def test_preserves_selection_on_toggle(self) -> None:
        """Test that selection is not affected by toggling."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
            selected_index=1,
        )

        next_state = ToggleImageUseCase().invoke(state, 0, False)

        assert next_state.selected_index == state.selected_index

    def test_handles_all_disabled(self) -> None:
        """Test toggling when all images are already disabled."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=False),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=False),
            ),
        )

        next_state = ToggleImageUseCase().invoke(state, 0, True)

        assert next_state.images[0].enabled is True
        assert next_state.images[1].enabled is False
