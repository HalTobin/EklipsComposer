"""Unit tests for UpdateGalleryViewModeUseCase."""

from eclipse_compositor.ui.state import GalleryViewMode, ScreenState
from eclipse_compositor.ui.use_cases import UpdateGalleryViewModeUseCase


class TestUpdateGalleryViewModeUseCase:
    """Test suite for UpdateGalleryViewModeUseCase."""

    def test_changes_view_mode(self) -> None:
        state = ScreenState(gallery_view_mode=GalleryViewMode.LIST_PREVIEW)

        next_state = UpdateGalleryViewModeUseCase().invoke(
            state, GalleryViewMode.ICON
        )

        assert next_state.gallery_view_mode == GalleryViewMode.ICON

    def test_returns_same_state_when_unchanged(self) -> None:
        state = ScreenState(gallery_view_mode=GalleryViewMode.LIST_SIMPLE)

        next_state = UpdateGalleryViewModeUseCase().invoke(
            state, GalleryViewMode.LIST_SIMPLE
        )

        assert next_state is state

    def test_accepts_string_value(self) -> None:
        state = ScreenState(gallery_view_mode=GalleryViewMode.LIST_PREVIEW)

        next_state = UpdateGalleryViewModeUseCase().invoke(state, "icon")

        assert next_state.gallery_view_mode == GalleryViewMode.ICON
