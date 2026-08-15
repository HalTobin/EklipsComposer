from pathlib import Path

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import (
    ClearImagesUseCase,
    LoadImagesUseCase,
    RemoveImageUseCase,
    ReorderImagesUseCase,
    ToggleImageUseCase,
    UseCases,
)


def test_toggle_image_use_case_updates_enabled_flag() -> None:
    state = ScreenState(
        images=(
            ImageItem(path=Path("/tmp/first.jpg"), enabled=True),
            ImageItem(path=Path("/tmp/second.jpg"), enabled=True),
        ),
        selected_index=1,
    )

    next_state = ToggleImageUseCase().invoke(state, 1, False)

    assert next_state.images[1].enabled is False
    assert next_state.selected_index == state.selected_index


def test_remove_image_use_case_keeps_selection_in_bounds() -> None:
    state = ScreenState(
        images=(
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/second.jpg")),
            ImageItem(path=Path("/tmp/third.jpg")),
        ),
        selected_index=1,
    )

    next_state = RemoveImageUseCase().invoke(state, (0, 2))

    assert [item.path for item in next_state.images] == [
        Path("/tmp/second.jpg")
    ]
    assert next_state.selected_index == 0


def test_reorder_images_use_case_preserves_selected_path() -> None:
    state = ScreenState(
        images=(
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/second.jpg")),
            ImageItem(path=Path("/tmp/third.jpg")),
        ),
        selected_index=1,
    )

    reordered = (
        ImageItem(path=Path("/tmp/third.jpg")),
        ImageItem(path=Path("/tmp/first.jpg")),
        ImageItem(path=Path("/tmp/second.jpg")),
    )

    next_state = ReorderImagesUseCase().invoke(state, reordered)

    assert [item.path for item in next_state.images] == [
        Path("/tmp/third.jpg"),
        Path("/tmp/first.jpg"),
        Path("/tmp/second.jpg"),
    ]
    assert next_state.selected_index == 2


def test_load_images_use_case_appends_unique_items() -> None:
    state = ScreenState(
        images=(ImageItem(path=Path("/tmp/first.jpg")),),
        selected_index=0,
    )

    imported = (
        ImageItem(path=Path("/tmp/second.jpg")),
        ImageItem(path=Path("/tmp/first.jpg")),
    )

    next_state = LoadImagesUseCase().invoke(state, imported)

    assert [item.path for item in next_state.images] == [
        Path("/tmp/first.jpg"),
        Path("/tmp/second.jpg"),
    ]
    assert next_state.selected_index == 0


def test_clear_images_use_case_resets_gallery_state() -> None:
    state = ScreenState(
        images=(ImageItem(path=Path("/tmp/first.jpg")),),
        selected_index=0,
        proxy_ready=True,
    )

    next_state = ClearImagesUseCase().invoke(state)

    assert next_state.images == ()
    assert next_state.selected_index is None
    assert next_state.proxy_ready is False


def test_use_cases_container_exposes_expected_attributes() -> None:
    use_cases = UseCases()

    assert isinstance(use_cases.load_images, LoadImagesUseCase)
    assert isinstance(use_cases.clear_images, ClearImagesUseCase)
    assert isinstance(use_cases.toggle_image, ToggleImageUseCase)
    assert isinstance(use_cases.remove_image, RemoveImageUseCase)
    assert isinstance(use_cases.reorder_images, ReorderImagesUseCase)
