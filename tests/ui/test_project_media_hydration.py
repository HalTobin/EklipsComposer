from pathlib import Path

from eclipse_compositor.project.domain.models import (
    ColorimetrySettings,
    CompositeSettings,
    MaskSettings,
    ProjectDocument,
    FrameRecord,
)
from eclipse_compositor.ui.project_mapping import state_from_document


def test_state_from_document_populates_project_and_canvas_media() -> None:
    document = ProjectDocument(
        version=1,
        composite=CompositeSettings(
            crop_size=1200,
            spacing=0.0,
            layout="arc",
            arc_angle=90.0,
            direction="horizontal",
            threshold=180,
            grid_columns=2,
            grid_rows=1,
        ),
        colorimetry=ColorimetrySettings(1.0, 1.0, 0.0, 1.0, 0.0),
        mask=MaskSettings(False, 0.9, 0.2),
        frames=(
            FrameRecord(file="alpha.jpg", enabled=True, favorite=True),
            FrameRecord(file="beta.jpg", enabled=False, favorite=False),
        ),
    )

    state = state_from_document(
        document,
        images=(
            __import__("eclipse_compositor.ui.state", fromlist=["ImageItem"]).ImageItem(path=Path("/tmp/alpha.jpg"), favorite=True),
            __import__("eclipse_compositor.ui.state", fromlist=["ImageItem"]).ImageItem(path=Path("/tmp/beta.jpg"), favorite=False),
        ),
        native_max=2400,
        project_path=Path("/tmp/project.vlt"),
        proxy_generation=1,
        preview_generation=1,
    )

    assert len(state.project_media) == 2
    assert state.project_media[0].path == Path("/tmp/alpha.jpg")
    assert state.project_media[0].title == "alpha.jpg"
    assert state.canvas_media == ()
