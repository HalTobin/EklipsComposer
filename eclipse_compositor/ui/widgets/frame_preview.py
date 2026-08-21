"""Backward-compatible re-export of FramePreview from the gallery package."""

from eclipse_compositor.ui.widgets.gallery.preview import (
    FramePreview,
    read_image_properties,
)

__all__ = ["FramePreview", "read_image_properties"]
