"""Tests for updating project gallery visibility."""

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.use_cases.update_project_gallery_hidden_use_case import (
    UpdateProjectGalleryHiddenUseCase,
)


def test_updates_project_gallery_visibility() -> None:
    use_case = UpdateProjectGalleryHiddenUseCase()
    state = ScreenState()

    updated = use_case.invoke(state, True)

    assert updated.project_gallery_hidden is True
    assert use_case.invoke(updated, True) is updated