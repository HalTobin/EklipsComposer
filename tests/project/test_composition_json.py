"""Unit tests for project document JSON serialization with various layouts."""

from __future__ import annotations

from pathlib import Path
import pytest

from eclipse_compositor.cv.layout import LayoutType
from eclipse_compositor.project.data.composition_json import (
    decode_composition,
    encode_composition,
)
from eclipse_compositor.project.domain.models import (
    ColorimetrySettings,
    CompositeSettings,
    FrameRecord,
    ManualDetection,
    MaskSettings,
    ProjectDocument,
)
from eclipse_compositor.ui.project_mapping import (
    blueprint_from_state,
    state_from_document,
)
from eclipse_compositor.ui.state import ScreenState


class TestCompositionJsonCircleLayout:
    """Test suite for circle layout serialization."""

    def test_encode_and_decode_circle_composition(self) -> None:
        doc = ProjectDocument(
            version=1,
            composite=CompositeSettings(
                crop_size=800,
                spacing=-0.15,
                layout="circle",
                arc_angle=120.0,
                direction="horizontal",
                threshold=180,
                grid_columns=3,
                grid_rows=2,
            ),
            colorimetry=ColorimetrySettings(
                contrast=1.0,
                saturation=1.0,
                brightness=0.0,
                gamma=1.0,
                temperature=0.0,
            ),
            mask=MaskSettings(enabled=False, size=0.9, feather=0.2),
            frames=(FrameRecord(file="res/frame_0.jpg", enabled=True, favorite=False),),
        )

        encoded = encode_composition(doc)
        assert '"layout": "circle"' in encoded

        decoded = decode_composition(encoded)
        assert decoded.composite.layout == "circle"

    def test_serializes_manual_detection_in_composition_json(self) -> None:
        doc = ProjectDocument(
            version=1,
            composite=CompositeSettings(
                crop_size=800,
                spacing=-0.15,
                layout="arc",
                arc_angle=120.0,
                direction="horizontal",
                threshold=180,
                grid_columns=3,
                grid_rows=2,
            ),
            colorimetry=ColorimetrySettings(
                contrast=1.0,
                saturation=1.0,
                brightness=0.0,
                gamma=1.0,
                temperature=0.0,
            ),
            mask=MaskSettings(enabled=False, size=0.9, feather=0.2),
            frames=(
                FrameRecord(
                    file="res/frame_0.jpg",
                    enabled=True,
                    favorite=False,
                    manual_detection=ManualDetection(
                        center=(100, 150),
                        radius=50.0,
                        area=7850.0,
                        confidence=0.95,
                    ),
                ),
            ),
        )

        encoded = encode_composition(doc)
        assert '"manual_detection"' in encoded

        decoded = decode_composition(encoded)
        assert decoded.frames[0].manual_detection == doc.frames[0].manual_detection

    def test_blueprint_from_state_and_state_from_document_circle(self) -> None:
        state = ScreenState(layout=LayoutType.CIRCLE)
        blueprint = blueprint_from_state(state)
        assert blueprint.composite.layout == "circle"

        doc = ProjectDocument(
            version=1,
            composite=blueprint.composite,
            colorimetry=blueprint.colorimetry,
            mask=blueprint.mask,
            frames=(),
        )
        loaded_state = state_from_document(
            doc,
            (),
            native_max=800,
            project_path=Path("/tmp/test.vlt"),
            proxy_generation=1,
            preview_generation=1,
        )
        assert loaded_state.layout == LayoutType.CIRCLE
