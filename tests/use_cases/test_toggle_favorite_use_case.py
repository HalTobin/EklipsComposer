"""Unit tests for ToggleFavoriteUseCase."""

from pathlib import Path

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import ToggleFavoriteUseCase


class TestToggleFavoriteUseCase:
    """Test suite for ToggleFavoriteUseCase."""

    def test_marks_frame_as_favorite(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
        )

        next_state = ToggleFavoriteUseCase().invoke(state, 0, True)

        assert next_state.images[0].favorite is True
        assert next_state.images[1].favorite is False

    def test_unmarks_frame_as_favorite(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg"), favorite=True),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
        )

        next_state = ToggleFavoriteUseCase().invoke(state, 0, False)

        assert next_state.images[0].favorite is False

    def test_ignores_out_of_range_index(self) -> None:
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
        )

        next_state = ToggleFavoriteUseCase().invoke(state, 5, True)

        assert next_state is state

    def test_preserves_selection(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
            selected_index=1,
        )

        next_state = ToggleFavoriteUseCase().invoke(state, 0, True)

        assert next_state.selected_index == 1
