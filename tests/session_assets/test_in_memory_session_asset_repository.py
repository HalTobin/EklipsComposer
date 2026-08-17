"""Unit tests for InMemorySessionAssetRepository."""

from pathlib import Path

import numpy as np

from eclipse_compositor.session_assets import InMemorySessionAssetRepository


def _frame(fill: int = 0) -> np.ndarray:
    return np.full((4, 4, 3), fill, dtype=np.uint8)


class TestProxyCache:
    """Test suite for proxy/shape storage and lookup."""

    def test_proxy_returns_none_for_unknown_path(self) -> None:
        repo = InMemorySessionAssetRepository()

        assert repo.proxy(Path("/tmp/missing.jpg")) is None

    def test_proxy_cache_is_a_live_shared_dict(self) -> None:
        """Workers write into the exposed dict by reference (background thread)."""
        repo = InMemorySessionAssetRepository()
        path = Path("/tmp/a.jpg")

        repo.proxy_cache[path] = _frame(10)
        repo.full_shapes[path] = (100, 200)

        assert repo.proxy(path) is not None
        assert repo.full_shapes[path] == (100, 200)


class TestDiscard:
    """Test suite for discard()."""

    def test_discard_drops_paths_not_in_keep_set(self) -> None:
        repo = InMemorySessionAssetRepository()
        keep = Path("/tmp/keep.jpg")
        drop = Path("/tmp/drop.jpg")
        repo.proxy_cache[keep] = _frame()
        repo.proxy_cache[drop] = _frame()
        repo.full_shapes[keep] = (10, 10)
        repo.full_shapes[drop] = (10, 10)

        repo.discard({keep})

        assert repo.proxy(keep) is not None
        assert repo.proxy(drop) is None
        assert drop not in repo.full_shapes

    def test_discard_with_empty_keep_clears_all_entries(self) -> None:
        repo = InMemorySessionAssetRepository()
        path = Path("/tmp/a.jpg")
        repo.proxy_cache[path] = _frame()
        repo.full_shapes[path] = (10, 10)

        repo.discard(set())

        assert repo.proxy_cache == {}
        assert repo.full_shapes == {}


class TestClear:
    """Test suite for clear()."""

    def test_clear_empties_caches(self) -> None:
        repo = InMemorySessionAssetRepository()
        path = Path("/tmp/a.jpg")
        repo.proxy_cache[path] = _frame()
        repo.full_shapes[path] = (10, 10)

        repo.clear()

        assert repo.proxy_cache == {}
        assert repo.full_shapes == {}

    def test_clear_removes_extraction_temp_dirs(self) -> None:
        repo = InMemorySessionAssetRepository()
        video_dir = repo.video_frame_dir()
        thumb_dir = repo.thumb_dir()
        staging_dir = repo.begin_open_staging()

        repo.clear()

        assert not video_dir.exists()
        assert not thumb_dir.exists()
        assert not staging_dir.exists()


class TestTempDirs:
    """Test suite for lazily-created scratch directories."""

    def test_video_frame_dir_is_created_and_memoized(self) -> None:
        repo = InMemorySessionAssetRepository()

        first = repo.video_frame_dir()
        second = repo.video_frame_dir()

        assert first == second
        assert first.is_dir()

    def test_thumb_dir_is_created_and_memoized(self) -> None:
        repo = InMemorySessionAssetRepository()

        first = repo.thumb_dir()
        second = repo.thumb_dir()

        assert first == second
        assert first.is_dir()

    def test_video_and_thumb_dirs_are_independent(self) -> None:
        repo = InMemorySessionAssetRepository()

        assert repo.video_frame_dir() != repo.thumb_dir()


class TestOpenStaging:
    """Test suite for the open-project staging lifecycle."""

    def test_begin_open_staging_creates_a_directory(self) -> None:
        repo = InMemorySessionAssetRepository()

        staging = repo.begin_open_staging()

        assert staging.is_dir()

    def test_begin_open_staging_discards_a_previous_staging_dir(self) -> None:
        repo = InMemorySessionAssetRepository()
        first = repo.begin_open_staging()

        second = repo.begin_open_staging()

        assert not first.exists()
        assert second.is_dir()
        assert first != second

    def test_discard_open_staging_removes_the_directory(self) -> None:
        repo = InMemorySessionAssetRepository()
        staging = repo.begin_open_staging()

        repo.discard_open_staging()

        assert not staging.exists()

    def test_discard_open_staging_is_a_no_op_when_nothing_staged(self) -> None:
        repo = InMemorySessionAssetRepository()

        repo.discard_open_staging()  # must not raise

    def test_commit_open_staging_swaps_in_new_caches(self) -> None:
        repo = InMemorySessionAssetRepository()
        repo.begin_open_staging()
        new_path = Path("/tmp/opened.jpg")
        new_proxy_cache = {new_path: _frame()}
        new_full_shapes = {new_path: (50, 50)}

        repo.commit_open_staging(new_proxy_cache, new_full_shapes)

        assert repo.proxy_cache is new_proxy_cache
        assert repo.full_shapes is new_full_shapes

    def test_commit_open_staging_promotes_staging_dir_to_project_dir(self) -> None:
        repo = InMemorySessionAssetRepository()
        staging = repo.begin_open_staging()

        repo.commit_open_staging({}, {})

        # The extracted files must still be on disk (now owned as the
        # project's resource dir) rather than deleted with the old staging.
        assert staging.is_dir()

    def test_commit_open_staging_clears_video_and_thumb_dirs(self) -> None:
        repo = InMemorySessionAssetRepository()
        video_dir = repo.video_frame_dir()
        thumb_dir = repo.thumb_dir()
        repo.begin_open_staging()

        repo.commit_open_staging({}, {})

        assert not video_dir.exists()
        assert not thumb_dir.exists()

    def test_commit_open_staging_replaces_a_prior_project_dir(self) -> None:
        repo = InMemorySessionAssetRepository()
        first_staging = repo.begin_open_staging()
        repo.commit_open_staging({}, {})

        second_staging = repo.begin_open_staging()
        repo.commit_open_staging({}, {})

        # Opening a second project must clean up the first one's resource dir.
        assert not first_staging.exists()
        assert second_staging.is_dir()


class TestClose:
    """Test suite for close()."""

    def test_close_removes_every_temp_dir(self) -> None:
        repo = InMemorySessionAssetRepository()
        video_dir = repo.video_frame_dir()
        thumb_dir = repo.thumb_dir()
        staging_dir = repo.begin_open_staging()

        repo.close()

        assert not video_dir.exists()
        assert not thumb_dir.exists()
        assert not staging_dir.exists()

    def test_close_is_idempotent(self) -> None:
        repo = InMemorySessionAssetRepository()
        repo.video_frame_dir()

        repo.close()
        repo.close()  # must not raise
