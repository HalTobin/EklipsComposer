"""Unit tests for SetAllEnabledUseCase."""

from pathlib import Path

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import SetAllEnabledUseCase


class TestSetAllEnabledUseCase:
    """Test suite for SetAllEnabledUseCase."""

    def test_enables_all_frames(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=False),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
            ),
        )

        next_state = SetAllEnabledUseCase().invoke(state, True)

        assert all(item.enabled for item in next_state.images)

    def test_disables_all_frames(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
            ),
        )

        next_state = SetAllEnabledUseCase().invoke(state, False)

        assert not any(item.enabled for item in next_state.images)

    def test_returns_same_state_when_no_change(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
                ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
            ),
        )

        next_state = SetAllEnabledUseCase().invoke(state, True)

        assert next_state is state

    def test_returns_same_state_when_empty(self) -> None:
        state = ScreenState()

        next_state = SetAllEnabledUseCase().invoke(state, True)

        assert next_state is state
