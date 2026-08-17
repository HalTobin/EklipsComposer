"""Repository contract for the session-scoped decoded-frame cache.

Implementations live in the data layer. Callers (the ViewModel, workers)
depend only on this contract, never on ``tempfile`` or dict internals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol

import numpy as np


class SessionAssetRepository(Protocol):
    """Owns decoded frame proxies, native shapes, and extraction temp dirs.

    Session-scoped only: never persisted, discarded on ``clear()``. This
    exists so the ViewModel orchestrates state transitions without holding
    raw pixel caches or ``tempfile`` handles itself.
    """

    @property
    def proxy_cache(self) -> dict[Path, np.ndarray]:
        """Downscaled preview proxy for each imported frame, keyed by source path."""

    @property
    def full_shapes(self) -> dict[Path, tuple[int, int]]:
        """Native ``(height, width)`` for each imported frame, keyed by source path."""

    def proxy(self, path: Path) -> np.ndarray | None:
        """Return the cached proxy for *path*, or ``None`` if not imported."""

    def discard(self, keep: Iterable[Path]) -> None:
        """Drop cached proxies/shapes for any path not in *keep*."""

    def clear(self) -> None:
        """Drop all cached data and extracted temp files (gallery cleared)."""

    def video_frame_dir(self) -> Path:
        """Directory that persists stills extracted from imported videos."""

    def thumb_dir(self) -> Path:
        """Directory that persists small gallery-list thumbnails."""

    def begin_open_staging(self) -> Path:
        """Start extracting a ``.vlt`` archive; return a fresh scratch directory."""

    def commit_open_staging(
        self,
        proxy_cache: dict[Path, np.ndarray],
        full_shapes: dict[Path, tuple[int, int]],
    ) -> None:
        """Adopt a successfully opened project.

        Swaps in *proxy_cache*/*full_shapes* and promotes the staging
        directory started by ``begin_open_staging`` to the live project's
        extracted-resource directory.
        """

    def discard_open_staging(self) -> None:
        """Delete a failed or cancelled open's scratch directory."""

    def close(self) -> None:
        """Release every temp directory (app shutdown / repository disposal)."""
