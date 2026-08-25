"""Unit and component tests for GalleryBar."""

from pathlib import Path
from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.state import GallerySortMode, GalleryViewMode, ImageItem, JobStatus, ScreenState
from eclipse_compositor.ui.widgets.gallery import GalleryBar


def _get_app():
    return QApplication.instance() or QApplication([])


def test_gallery_bar_initialization() -> None:
    _get_app()
    gallery = GalleryBar()
    assert gallery.objectName() == "gallery"
    assert gallery.header is not None
    assert gallery.toolbar is not None
    assert gallery.list is not None
    assert gallery.frame_preview is not None


def test_gallery_bar_render_state() -> None:
    _get_app()
    gallery = GalleryBar()

    images = (
        ImageItem(path=Path("img1.jpg"), enabled=True, detection_ok=True, favorite=False),
        ImageItem(path=Path("img2.jpg"), enabled=False, detection_ok=True, favorite=True),
        ImageItem(path=Path("img3.jpg"), enabled=True, detection_ok=False, favorite=True),
    )

    state = ScreenState(
        images=images,
        selected_index=1,
        gallery_view_mode=GalleryViewMode.LIST_SIMPLE,
        gallery_sort_mode=GallerySortMode.DATE_TAKEN,
        gallery_show_only_favorites=False,
        import_status=JobStatus.IDLE,
    )

    gallery.render(state)

    assert gallery.list.count() == 3
    assert "2/3" in gallery.header._count_badge.text()
    assert "★ 2" in gallery.header._count_badge.text()
    assert gallery.toolbar.view_mode.currentIndex() == 1
    assert gallery.toolbar.sort_mode.currentData() == GallerySortMode.DATE_TAKEN
    assert gallery.toolbar.favorites_btn.isChecked() is False


def test_gallery_bar_favorites_filter_render() -> None:
    _get_app()
    gallery = GalleryBar()

    images = (
        ImageItem(path=Path("img1.jpg"), enabled=True, detection_ok=True, favorite=False),
        ImageItem(path=Path("img2.jpg"), enabled=True, detection_ok=True, favorite=True),
        ImageItem(path=Path("img3.jpg"), enabled=True, detection_ok=True, favorite=True),
    )

    state = ScreenState(
        images=images,
        selected_index=0,
        gallery_view_mode=GalleryViewMode.LIST_PREVIEW,
        gallery_sort_mode=GallerySortMode.TITLE,
        gallery_show_only_favorites=True,
    )

    gallery.render(state)

    # 2 favorites + 1 selected non-favorite = 3 visible items
    assert gallery.list.count() == 3
    assert gallery.toolbar.favorites_btn.isChecked() is True


def test_canvas_media_reflects_enabled_composition_frames() -> None:
    _get_app()
    gallery = GalleryBar()
    images = (
        ImageItem(path=Path("first.jpg"), enabled=True, detection_ok=True),
        ImageItem(path=Path("hidden.jpg"), enabled=False, detection_ok=True),
        ImageItem(path=Path("third.jpg"), enabled=True, detection_ok=True),
    )

    gallery.render(ScreenState(images=images))

    assert gallery.canvas_model.rowCount() == 2
    assert gallery.canvas_model.data(gallery.canvas_model.index(0)) == "first.jpg"
    assert gallery.canvas_model.data(gallery.canvas_model.index(1)) == "third.jpg"
