"""Unit tests for UpdateGalleryShowOnlyFavoritesUseCase."""

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.use_cases import UpdateGalleryShowOnlyFavoritesUseCase


class TestUpdateGalleryShowOnlyFavoritesUseCase:
    """Test suite for UpdateGalleryShowOnlyFavoritesUseCase."""

    def test_enables_filter(self) -> None:
        state = ScreenState(gallery_show_only_favorites=False)

        next_state = UpdateGalleryShowOnlyFavoritesUseCase().invoke(state, True)

        assert next_state.gallery_show_only_favorites is True

    def test_disables_filter(self) -> None:
        state = ScreenState(gallery_show_only_favorites=True)

        next_state = UpdateGalleryShowOnlyFavoritesUseCase().invoke(state, False)

        assert next_state.gallery_show_only_favorites is False

    def test_returns_same_state_when_unchanged(self) -> None:
        state = ScreenState(gallery_show_only_favorites=True)

        next_state = UpdateGalleryShowOnlyFavoritesUseCase().invoke(state, True)

        assert next_state is state
