"""Use case for reordering items already added to the canvas."""

from __future__ import annotations

from dataclasses import dataclass

from eclipse_compositor.ui.state import CanvasItem


@dataclass(frozen=True)
class ReorderCanvasMediaUseCase:
    """Move one canvas item from one position to another."""

    def invoke(
        self,
        canvas_media: tuple[CanvasItem, ...],
        from_index: int,
        to_index: int,
    ) -> tuple[CanvasItem, ...]:
        if not (0 <= from_index < len(canvas_media)):
            return canvas_media
        if not (0 <= to_index < len(canvas_media)):
            return canvas_media
        if from_index == to_index:
            return canvas_media

        items = list(canvas_media)
        item = items.pop(from_index)
        items.insert(to_index, item)
        return tuple(items)
