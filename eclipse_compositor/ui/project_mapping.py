"""Map ScreenState to/from the project domain snapshot."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.project.domain.models import (
    ColorimetrySettings,
    CompositeSettings,
    FrameSource,
    ManualDetection,
    MaskSettings,
    ProjectBlueprint,
    ProjectDocument,
)
from eclipse_compositor.ui.state import MIN_RESOLUTION, ImageItem, JobStatus, default_state


def blueprint_from_state(state: ScreenState) -> ProjectBlueprint:
    """Build a persistable blueprint from the current screen state."""
    return ProjectBlueprint(
        composite=CompositeSettings(
            crop_size=state.crop_size,
            spacing=state.spacing,
            layout=state.layout.value,
            arc_angle=state.arc_angle,
            direction=state.direction.value,
            threshold=state.threshold,
            grid_columns=state.grid_columns,
            grid_rows=state.grid_rows,
            margin_x=state.margin_x,
            margin_y=state.margin_y,
            margin_linked=state.margin_linked,
        ),
        colorimetry=ColorimetrySettings(
            contrast=state.contrast,
            saturation=state.saturation,
            brightness=state.brightness,
            gamma=state.gamma,
            temperature=state.temperature,
        ),
        mask=MaskSettings(
            enabled=state.mask_enabled,
            size=state.mask_size,
            feather=state.mask_feather,
        ),
        frames=tuple(
            FrameSource(
                source_path=item.path,
                enabled=item.enabled,
                favorite=item.favorite,
                manual_detection=_serialize_manual_detection(item.manual_detection),
            )
            for item in state.images
        ),
    )


def state_from_document(
    document: ProjectDocument,
    images: tuple[ImageItem, ...],
    *,
    native_max: int,
    project_path: Path,
    proxy_generation: int,
    preview_generation: int,
) -> ScreenState:
    """Replace persistable fields with *document* and loaded *images*."""
    composite = document.composite
    color = document.colorimetry
    mask = document.mask
    crop = max(MIN_RESOLUTION, min(composite.crop_size, native_max))
    selected = 0 if images else None
    return replace(
        default_state(),
        images=images,
        crop_size=crop,
        spacing=composite.spacing,
        layout=LayoutType(composite.layout),
        arc_angle=composite.arc_angle,
        direction=LayoutDirection(composite.direction),
        threshold=composite.threshold,
        grid_columns=composite.grid_columns,
        grid_rows=composite.grid_rows,
        native_max_resolution=native_max,
        proxy_ready=bool(images),
        last_project_path=project_path,
        import_status=JobStatus.IDLE,
        export_status=JobStatus.IDLE,
        preview_status=JobStatus.IDLE,
        progress=1.0,
        status_message=f"Opened {project_path.name}.",
        error_message=None,
        selected_index=selected,
        contrast=color.contrast,
        saturation=color.saturation,
        brightness=color.brightness,
        gamma=color.gamma,
        temperature=color.temperature,
        mask_enabled=mask.enabled,
        mask_size=mask.size,
        mask_feather=mask.feather,
        margin_linked=composite.margin_linked,
        margin_x=composite.margin_x,
        margin_y=composite.margin_y,
        _proxy_generation=proxy_generation,
        _preview_generation=preview_generation,
    )


def _serialize_manual_detection(detection: DiscDetection | None) -> ManualDetection | None:
    if detection is None:
        return None
    return ManualDetection(
        center=detection.center,
        radius=detection.radius,
        area=detection.area,
        confidence=detection.confidence,
    )
