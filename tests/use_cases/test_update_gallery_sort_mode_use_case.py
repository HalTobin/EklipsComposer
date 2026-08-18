"""Unit tests for UpdateGallerySortModeUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import GallerySortMode, ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import UpdateGallerySortModeUseCase


class TestUpdateGallerySortModeUseCase:
    """Test suite for UpdateGallerySortModeUseCase."""

    def test_sorts_by_title(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/b.jpg")),
                ImageItem(path=Path("/tmp/a.jpg")),
            ),
            selected_index=0,
        )

        next_state = UpdateGallerySortModeUseCase().invoke(
            state, GallerySortMode.TITLE
        )

        assert [item.path.name for item in next_state.images] == ["a.jpg", "b.jpg"]
        assert next_state.gallery_sort_mode == GallerySortMode.TITLE

    def test_sorts_by_date_taken(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/b.jpg")),
                ImageItem(path=Path("/tmp/a.jpg")),
            ),
            gallery_sort_mode=GallerySortMode.TITLE,
        )

        next_state = UpdateGallerySortModeUseCase().invoke(
            state, GallerySortMode.DATE_TAKEN
        )

        assert next_state.gallery_sort_mode == GallerySortMode.DATE_TAKEN

    def test_preserves_selection_after_sort(self) -> None:
        selected = ImageItem(path=Path("/tmp/b.jpg"))
        state = ScreenState(
            images=(
                selected,
                ImageItem(path=Path("/tmp/a.jpg")),
            ),
            selected_index=0,
        )

        next_state = UpdateGallerySortModeUseCase().invoke(
            state, GallerySortMode.TITLE
        )

        assert next_state.selected_index == 1
        assert next_state.images[next_state.selected_index].path == selected.path

    def test_returns_same_state_when_mode_unchanged_and_images_sorted(self) -> None:
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/a.jpg")),
                ImageItem(path=Path("/tmp/b.jpg")),
            ),
            gallery_sort_mode=GallerySortMode.TITLE,
        )

        next_state = UpdateGallerySortModeUseCase().invoke(
            state, GallerySortMode.TITLE
        )

        assert next_state is state
