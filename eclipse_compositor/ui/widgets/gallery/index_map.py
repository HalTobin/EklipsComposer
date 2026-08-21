"""Index mapping and filtering logic for the gallery frame list."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from eclipse_compositor.ui.state import ImageItem


@dataclass(frozen=True)
class DisplayIndexMap:
    """Calculates visible indices and handles translation between visible rows and original image indices."""

    images: tuple[ImageItem, ...] = ()
    show_only_favorites: bool = False
    selected_index: int | None = None
    display_indices: list[int] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        indices = self._compute_display_indices()
        object.__setattr__(self, "display_indices", indices)

    def _compute_display_indices(self) -> list[int]:
        if not self.show_only_favorites:
            return list(range(len(self.images)))
        selected = self.selected_index
        return [
            idx
            for idx, item in enumerate(self.images)
            if item.favorite or idx == selected
        ]

    @property
    def visible_count(self) -> int:
        """Number of items currently visible in the filtered list."""
        return len(self.display_indices)

    @property
    def is_filtered(self) -> bool:
        """True when a filter hides some items in the collection."""
        return len(self.display_indices) != len(self.images)

    @property
    def can_reorder(self) -> bool:
        """Reordering is only permitted when the entire list is displayed."""
        return not self.is_filtered

    def to_original(self, visible_row: int) -> int | None:
        """Convert a visible list row index into the original index in `images`."""
        if 0 <= visible_row < len(self.display_indices):
            return self.display_indices[visible_row]
        return None

    def to_visible(self, original_index: int | None) -> int | None:
        """Convert an original image index into the visible list row index."""
        if original_index is None:
            return None
        try:
            return self.display_indices.index(original_index)
        except ValueError:
            return None

    def selected_original_indices(self, visible_rows: Iterable[int]) -> tuple[int, ...]:
        """Convert a sequence of visible selected row indices to original indices."""
        return tuple(
            idx
            for r in visible_rows
            if (idx := self.to_original(r)) is not None
        )

    def reorder_items(
        self,
        visible_rows_data: Sequence[tuple[Path, bool]],
    ) -> tuple[ImageItem, ...] | None:
        """Reconstruct reordered ImageItem tuple based on reordered row (path, enabled) data.

        Returns None if reordering is not possible (e.g. filtered) or if order did not change.
        """
        if not self.can_reorder:
            return None

        ordered: list[ImageItem] = []
        item_by_path = {item.path: item for item in self.images}

        for path, enabled in visible_rows_data:
            base = item_by_path.get(path)
            if base is None:
                continue
            ordered.append(
                ImageItem(
                    path=base.path,
                    enabled=enabled,
                    detection_ok=base.detection_ok,
                    thumbnail_path=base.thumbnail_path,
                    favorite=base.favorite,
                )
            )

        if ordered and tuple(ordered) != self.images:
            return tuple(ordered)
        return None
