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

    gallery.render(
        ScreenState(
            images=images,
            canvas_gallery_view_mode=GalleryViewMode.LIST_SIMPLE,
        )
    )

    assert gallery.canvas_list.count() == 2
    assert gallery.canvas_toolbar.view_mode.currentIndex() == 1
    assert len(gallery.canvas_toolbar.view_mode._buttons) == 2
    assert gallery.canvas_list._delegate._show_enabled_control is False

    selected_indices: list[int] = []
    gallery.select_image.connect(selected_indices.append)
    gallery.canvas_list.row_selected.emit(1)
    assert selected_indices == [2]

    reordered_images: list[tuple[ImageItem, ...]] = []
    gallery.reorder_images.connect(reordered_images.append)
    gallery.canvas_list.rows_reordered.emit(
        ((Path("third.jpg"), True), (Path("first.jpg"), True))
    )
    assert [item.path.name for item in reordered_images[0]] == [
        "third.jpg",
        "hidden.jpg",
        "first.jpg",
    ]

    disabled_frames: list[tuple[int, bool]] = []
    gallery.toggle_image.connect(
        lambda index, enabled: disabled_frames.append((index, enabled))
    )
    gallery.canvas_list.remove_requested.emit((0,))
    assert disabled_frames == [(2, False)]
