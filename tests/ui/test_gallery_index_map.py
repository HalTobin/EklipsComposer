"""Unit tests for DisplayIndexMap in the gallery package."""

from pathlib import Path

from eclipse_compositor.ui.state import ImageItem
from eclipse_compositor.ui.widgets.gallery.index_map import DisplayIndexMap


def _create_sample_items(count: int = 5, favorite_indices: tuple[int, ...] = ()) -> tuple[ImageItem, ...]:
    return tuple(
        ImageItem(
            path=Path(f"img_{i}.jpg"),
            enabled=True,
            detection_ok=True,
            thumbnail_path=None,
            favorite=(i in favorite_indices),
        )
        for i in range(count)
    )


def test_unfiltered_index_map() -> None:
    items = _create_sample_items(5)
    mapper = DisplayIndexMap(images=items, show_only_favorites=False, selected_index=None)

    assert mapper.visible_count == 5
    assert mapper.is_filtered is False
    assert mapper.can_reorder is True
    assert mapper.display_indices == [0, 1, 2, 3, 4]

    for i in range(5):
        assert mapper.to_original(i) == i
        assert mapper.to_visible(i) == i

    assert mapper.to_original(99) is None
    assert mapper.to_visible(99) is None
    assert mapper.selected_original_indices([1, 3]) == (1, 3)


def test_filtered_by_favorites_with_no_selection() -> None:
    items = _create_sample_items(5, favorite_indices=(1, 3))
    mapper = DisplayIndexMap(images=items, show_only_favorites=True, selected_index=None)

    assert mapper.visible_count == 2
    assert mapper.is_filtered is True
    assert mapper.can_reorder is False
    assert mapper.display_indices == [1, 3]

    assert mapper.to_original(0) == 1
    assert mapper.to_original(1) == 3
    assert mapper.to_visible(1) == 0
    assert mapper.to_visible(3) == 1
    assert mapper.to_visible(0) is None  # not favorite, not selected


def test_filtered_by_favorites_keeps_selected_non_favorite() -> None:
    items = _create_sample_items(5, favorite_indices=(1, 4))
    # Select item 2 which is not a favorite
    mapper = DisplayIndexMap(images=items, show_only_favorites=True, selected_index=2)

    assert mapper.display_indices == [1, 2, 4]
    assert mapper.visible_count == 3
    assert mapper.to_visible(2) == 1


def test_reorder_items_unfiltered() -> None:
    items = _create_sample_items(3)
    mapper = DisplayIndexMap(images=items, show_only_favorites=False, selected_index=None)

    reordered_rows = [
        (Path("img_2.jpg"), True),
        (Path("img_0.jpg"), True),
        (Path("img_1.jpg"), True),
    ]

    result = mapper.reorder_items(reordered_rows)
    assert result is not None
    assert [it.path.name for it in result] == ["img_2.jpg", "img_0.jpg", "img_1.jpg"]


def test_reorder_items_prohibited_when_filtered() -> None:
    items = _create_sample_items(4, favorite_indices=(0, 2))
    mapper = DisplayIndexMap(images=items, show_only_favorites=True, selected_index=None)

    reordered_rows = [
        (Path("img_2.jpg"), True),
        (Path("img_0.jpg"), True),
    ]

    result = mapper.reorder_items(reordered_rows)
    assert result is None
