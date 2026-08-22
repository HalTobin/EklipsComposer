"""Encode and decode ``composition.json`` (data-layer serialization)."""

from __future__ import annotations

import json
from typing import Any

from eclipse_compositor.project.domain.errors import ProjectFormatError
from eclipse_compositor.project.domain.models import (
    ALLOWED_DIRECTIONS,
    ALLOWED_LAYOUTS,
    FORMAT_ID,
    FORMAT_VERSION,
    ColorimetrySettings,
    CompositeSettings,
    FrameRecord,
    ManualDetection,
    MaskSettings,
    ProjectDocument,
)


def encode_composition(document: ProjectDocument) -> str:
    """Serialize *document* to a UTF-8 JSON string."""
    payload = {
        "format": FORMAT_ID,
        "version": document.version,
        "composite": {
            "crop_size": document.composite.crop_size,
            "spacing": document.composite.spacing,
            "layout": document.composite.layout,
            "arc_angle": document.composite.arc_angle,
            "direction": document.composite.direction,
            "threshold": document.composite.threshold,
            "grid_columns": document.composite.grid_columns,
            "grid_rows": document.composite.grid_rows,
            "margin_x": document.composite.margin_x,
            "margin_y": document.composite.margin_y,
            "margin_linked": document.composite.margin_linked,
        },
        "colorimetry": {
            "contrast": document.colorimetry.contrast,
            "saturation": document.colorimetry.saturation,
            "brightness": document.colorimetry.brightness,
            "gamma": document.colorimetry.gamma,
            "temperature": document.colorimetry.temperature,
        },
        "mask": {
            "enabled": document.mask.enabled,
            "size": document.mask.size,
            "feather": document.mask.feather,
        },
        "frames": [
            {
                "file": frame.file,
                "enabled": frame.enabled,
                "favorite": frame.favorite,
                "manual_detection": _encode_manual_detection(frame.manual_detection),
            }
            for frame in document.frames
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def decode_composition(raw: str) -> ProjectDocument:
    """Parse *raw* JSON into a ``ProjectDocument``.

    Args:
        raw: Contents of ``composition.json``.

    Raises:
        ProjectFormatError: If the document is missing fields or invalid.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProjectFormatError(f"composition.json is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProjectFormatError("composition.json must be a JSON object.")
    fmt = data.get("format")
    if fmt != FORMAT_ID:
        raise ProjectFormatError(
            f"Unknown project format {fmt!r}; expected {FORMAT_ID!r}."
        )
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ProjectFormatError("composition.json is missing a numeric version.")
    if version > FORMAT_VERSION:
        raise ProjectFormatError(
            f"Project version {version} is newer than this app "
            f"(supports up to {FORMAT_VERSION})."
        )
    if version < 1:
        raise ProjectFormatError(f"Unsupported project version: {version}.")
    composite = _parse_composite(data.get("composite"))
    colorimetry = _parse_colorimetry(data.get("colorimetry"))
    mask = _parse_mask(data.get("mask"))
    frames = _parse_frames(data.get("frames"))
    return ProjectDocument(
        version=version,
        composite=composite,
        colorimetry=colorimetry,
        mask=mask,
        frames=frames,
    )


def _encode_manual_detection(detection: ManualDetection | None) -> dict | None:
    if detection is None:
        return None
    return {
        "center": [detection.center[0], detection.center[1]],
        "radius": detection.radius,
        "area": detection.area,
        "confidence": detection.confidence,
    }


def _parse_manual_detection(value: object | None) -> ManualDetection | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ProjectFormatError("manual_detection must be an object or null.")
    center = value.get("center")
    if (
        not isinstance(center, list)
        or len(center) != 2
        or any(not isinstance(c, int) or isinstance(c, bool) for c in center)
    ):
        raise ProjectFormatError("manual_detection.center must be a two-element integer array.")
    radius = _as_float(value.get("radius"), "manual_detection.radius")
    area = _as_float(value.get("area"), "manual_detection.area")
    confidence = _as_float(value.get("confidence"), "manual_detection.confidence")
    return ManualDetection(
        center=(center[0], center[1]),
        radius=radius,
        area=area,
        confidence=confidence,
    )


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectFormatError(f"composition.json is missing object {name!r}.")
    return value


def _as_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProjectFormatError(f"{name} must be an integer.")
    return int(value)


def _as_float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectFormatError(f"{name} must be a number.")
    return float(value)


def _as_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ProjectFormatError(f"{name} must be a boolean.")
    return value


def _as_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProjectFormatError(f"{name} must be a non-empty string.")
    return value


def _optional_int(data: dict[str, Any], key: str, default: int, name: str) -> int:
    if key not in data or data[key] is None:
        return default
    return _as_int(data[key], name)


def _optional_bool(data: dict[str, Any], key: str, default: bool, name: str) -> bool:
    if key not in data or data[key] is None:
        return default
    return _as_bool(data[key], name)


def _parse_composite(value: Any) -> CompositeSettings:
    data = _require_dict(value, "composite")
    layout = _as_str(data.get("layout"), "composite.layout")
    if layout not in ALLOWED_LAYOUTS:
        raise ProjectFormatError(f"Unknown layout: {layout!r}.")
    direction = _as_str(data.get("direction"), "composite.direction")
    if direction not in ALLOWED_DIRECTIONS:
        raise ProjectFormatError(f"Unknown direction: {direction!r}.")
    return CompositeSettings(
        crop_size=_as_int(data.get("crop_size"), "composite.crop_size"),
        spacing=_as_float(data.get("spacing"), "composite.spacing"),
        layout=layout,
        arc_angle=_as_float(data.get("arc_angle"), "composite.arc_angle"),
        direction=direction,
        threshold=_as_int(data.get("threshold"), "composite.threshold"),
        grid_columns=_as_int(data.get("grid_columns"), "composite.grid_columns"),
        grid_rows=_as_int(data.get("grid_rows"), "composite.grid_rows"),
        margin_x=_optional_int(data, "margin_x", 40, "composite.margin_x"),
        margin_y=_optional_int(data, "margin_y", 40, "composite.margin_y"),
        margin_linked=_optional_bool(
            data, "margin_linked", True, "composite.margin_linked"
        ),
    )


def _parse_colorimetry(value: Any) -> ColorimetrySettings:
    data = _require_dict(value, "colorimetry")
    return ColorimetrySettings(
        contrast=_as_float(data.get("contrast"), "colorimetry.contrast"),
        saturation=_as_float(data.get("saturation"), "colorimetry.saturation"),
        brightness=_as_float(data.get("brightness"), "colorimetry.brightness"),
        gamma=_as_float(data.get("gamma"), "colorimetry.gamma"),
        temperature=_as_float(data.get("temperature"), "colorimetry.temperature"),
    )


def _parse_mask(value: Any) -> MaskSettings:
    data = _require_dict(value, "mask")
    return MaskSettings(
        enabled=_as_bool(data.get("enabled"), "mask.enabled"),
        size=_as_float(data.get("size"), "mask.size"),
        feather=_as_float(data.get("feather"), "mask.feather"),
    )


def _parse_frames(value: Any) -> tuple[FrameRecord, ...]:
    if not isinstance(value, list):
        raise ProjectFormatError("composition.json is missing a frames array.")
    frames: list[FrameRecord] = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise ProjectFormatError(f"frames[{i}] must be an object.")
        file_name = _as_str(item.get("file"), f"frames[{i}].file").replace("\\", "/")
        parts = [part for part in file_name.split("/") if part]
        if file_name.startswith("/") or ".." in parts:
            raise ProjectFormatError(f"frames[{i}].file is not a safe relative path.")
        frames.append(
            FrameRecord(
                file=file_name,
                enabled=_as_bool(item.get("enabled"), f"frames[{i}].enabled"),
                favorite=_optional_bool(
                    item, "favorite", False, f"frames[{i}].favorite"
                ),
                manual_detection=_parse_manual_detection(item.get("manual_detection")),
            )
        )
    return tuple(frames)
