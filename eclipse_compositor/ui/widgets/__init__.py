"""Reusable Qt widgets for the compositor UI."""

from eclipse_compositor.ui.widgets.about_dialog import (
    AboutDialog,
    LicensesDialog,
    show_about_dialog,
    show_licenses_dialog,
)
from eclipse_compositor.ui.widgets.frame_preview import FramePreview
from eclipse_compositor.ui.widgets.fullscreen_preview import FullscreenPreview
from eclipse_compositor.ui.widgets.gallery import GalleryBar
from eclipse_compositor.ui.widgets.job_overlay import JobOverlay
from eclipse_compositor.ui.widgets.sidebar import Sidebar
from eclipse_compositor.ui.widgets.viewport import PreviewViewport, ViewportPane
from eclipse_compositor.ui.widgets.video_import_dialog import (
    VideoImportDialog,
    confirm_video_import,
)

__all__ = [
    "AboutDialog",
    "FramePreview",
    "FullscreenPreview",
    "GalleryBar",
    "JobOverlay",
    "LicensesDialog",
    "PreviewViewport",
    "Sidebar",
    "VideoImportDialog",
    "ViewportPane",
    "confirm_video_import",
    "show_about_dialog",
    "show_licenses_dialog",
]
