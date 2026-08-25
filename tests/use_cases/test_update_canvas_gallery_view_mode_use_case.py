from eclipse_compositor.ui.state import GalleryViewMode, ScreenState
from eclipse_compositor.ui.use_cases.update_canvas_gallery_view_mode_use_case import (
    UpdateCanvasGalleryViewModeUseCase,
)


def test_changes_canvas_view_mode_without_affecting_project_gallery() -> None:
    state = ScreenState(gallery_view_mode=GalleryViewMode.ICON)

    updated = UpdateCanvasGalleryViewModeUseCase().invoke(
        state,
        GalleryViewMode.LIST_PREVIEW,
    )

    assert updated.canvas_gallery_view_mode is GalleryViewMode.LIST_PREVIEW
    assert updated.gallery_view_mode is GalleryViewMode.ICON


def test_returns_existing_state_for_current_canvas_view_mode() -> None:
    state = ScreenState(canvas_gallery_view_mode=GalleryViewMode.LIST_SIMPLE)

    updated = UpdateCanvasGalleryViewModeUseCase().invoke(
        state,
        GalleryViewMode.LIST_SIMPLE,
    )

    assert updated is state


def test_icon_mode_falls_back_to_compact_canvas_list() -> None:
    updated = UpdateCanvasGalleryViewModeUseCase().invoke(
        ScreenState(),
        GalleryViewMode.ICON,
    )

    assert updated.canvas_gallery_view_mode is GalleryViewMode.LIST_SIMPLE
