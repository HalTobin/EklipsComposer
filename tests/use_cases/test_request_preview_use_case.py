"""Unit tests for RequestPreviewUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import RequestPreviewUseCase


class TestRequestPreviewUseCase:
    """Test suite for RequestPreviewUseCase."""

    def test_returns_state_unchanged(self) -> None:
        """Test that request_preview is a signal-only use case that returns state unchanged."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/test.jpg")),),
            preview_status=None,
        )

        next_state = RequestPreviewUseCase().invoke(state)

        assert next_state is state

    def test_is_idempotent(self) -> None:
        """Test that calling multiple times has no effect."""
        state = ScreenState()

        next_state1 = RequestPreviewUseCase().invoke(state)
        next_state2 = RequestPreviewUseCase().invoke(next_state1)

        assert next_state1 is state
        assert next_state2 is state

    def test_works_with_empty_gallery(self) -> None:
        """Test that request_preview works even with no images."""
        state = ScreenState(images=())

        next_state = RequestPreviewUseCase().invoke(state)

        assert next_state is state
