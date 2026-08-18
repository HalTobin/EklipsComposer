"""Zip-backed ``.vlt`` project store."""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from eclipse_compositor.project.data.composition_json import (
    decode_composition,
    encode_composition,
)
from eclipse_compositor.project.domain.errors import ProjectFormatError, ProjectIoError
from eclipse_compositor.project.domain.models import (
    COMPOSITION_FILENAME,
    FORMAT_VERSION,
    RESOURCE_DIR,
    FrameRecord,
    LoadedProject,
    ProjectBlueprint,
    ProjectDocument,
)
from eclipse_compositor.project.domain.repository import ProgressCallback

_UNSAFE_STEM = re.compile(r"[^\w.\-]+", re.UNICODE)


class ZipProjectRepository:
    """Persist projects as zip archives with ``composition.json`` and ``res/``."""

    def save(
        self,
        blueprint: ProjectBlueprint,
        archive_path: Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        """Pack *blueprint* into *archive_path* (atomic replace)."""
        dest = Path(archive_path)
        missing = [
            frame.source_path
            for frame in blueprint.frames
            if not frame.source_path.is_file()
        ]
        if missing:
            preview = ", ".join(path.name for path in missing[:5])
            extra = f" (+{len(missing) - 5} more)" if len(missing) > 5 else ""
            raise ProjectIoError(f"Missing source image(s): {preview}{extra}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = dest.with_name(dest.name + ".tmp")
        total = max(1, len(blueprint.frames) + 1)
        try:
            records: list[FrameRecord] = []
            used_names: set[str] = set()
            with zipfile.ZipFile(
                tmp_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            ) as zf:
                for i, frame in enumerate(blueprint.frames, start=1):
                    name = _unique_res_name(i, frame.source_path, used_names)
                    used_names.add(name)
                    arcname = f"{RESOURCE_DIR}/{name}"
                    _report(
                        progress,
                        (i - 1) / total,
                        f"Packing {frame.source_path.name}…",
                    )
                    zf.write(frame.source_path, arcname=arcname)
                    records.append(
                        FrameRecord(file=arcname, enabled=frame.enabled, favorite=frame.favorite)
                    )
                document = ProjectDocument(
                    version=FORMAT_VERSION,
                    composite=blueprint.composite,
                    colorimetry=blueprint.colorimetry,
                    mask=blueprint.mask,
                    frames=tuple(records),
                )
                _report(progress, (total - 1) / total, "Writing composition.json…")
                zf.writestr(COMPOSITION_FILENAME, encode_composition(document))
            tmp_path.replace(dest)
            _report(progress, 1.0, f"Saved {dest.name}")
        except InterruptedError:
            _unlink_quiet(tmp_path)
            raise
        except (ProjectFormatError, ProjectIoError):
            _unlink_quiet(tmp_path)
            raise
        except (OSError, zipfile.BadZipFile) as exc:
            _unlink_quiet(tmp_path)
            raise ProjectIoError(str(exc)) from exc

    def load(self, archive_path: Path, extract_dir: Path) -> LoadedProject:
        """Extract *archive_path* into *extract_dir* and return resolved frames."""
        src = Path(archive_path)
        root = Path(extract_dir)
        try:
            root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(src, mode="r") as zf:
                names = {_normalize_member(name) for name in zf.namelist()}
                if COMPOSITION_FILENAME not in names:
                    raise ProjectFormatError(
                        "Archive is missing composition.json."
                    )
                raw = zf.read(_member_key(zf, COMPOSITION_FILENAME))
                document = decode_composition(raw.decode("utf-8-sig"))
                json_dest = _safe_dest(root, COMPOSITION_FILENAME)
                json_dest.write_bytes(raw)
                frame_paths: list[Path] = []
                for frame in document.frames:
                    member = _normalize_member(frame.file)
                    if member not in names:
                        raise ProjectFormatError(
                            f"Archive is missing frame {frame.file!r}."
                        )
                    dest = _safe_dest(root, member)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(_member_key(zf, member)) as inbound, dest.open(
                        "wb"
                    ) as outbound:
                        shutil.copyfileobj(inbound, outbound)
                    frame_paths.append(dest)
        except ProjectFormatError:
            raise
        except zipfile.BadZipFile as exc:
            raise ProjectFormatError("File is not a valid EklipsComposer project.") from exc
        except OSError as exc:
            raise ProjectIoError(str(exc)) from exc
        return LoadedProject(
            document=document,
            frame_paths=tuple(frame_paths),
            extract_root=root,
        )


def _report(
    progress: ProgressCallback | None, fraction: float, message: str
) -> None:
    if progress is not None:
        progress(fraction, message)


def _unlink_quiet(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _sanitize_stem(stem: str) -> str:
    cleaned = _UNSAFE_STEM.sub("_", stem).strip("._")
    if not cleaned:
        return "frame"
    return cleaned[:80]


def _unique_res_name(index: int, source: Path, used: set[str]) -> str:
    suffix = source.suffix
    stem = _sanitize_stem(source.stem)
    candidate = f"{index:04d}_{stem}{suffix}"
    if candidate not in used:
        return candidate
    extra = 2
    while True:
        candidate = f"{index:04d}_{stem}_{extra}{suffix}"
        if candidate not in used:
            return candidate
        extra += 1


def _normalize_member(name: str) -> str:
    return name.replace("\\", "/").lstrip("./")


def _member_key(zf: zipfile.ZipFile, normalized: str) -> str:
    """Return the original zip member name matching *normalized*."""
    for name in zf.namelist():
        if _normalize_member(name) == normalized:
            return name
    raise ProjectFormatError(f"Archive is missing {normalized!r}.")


def _safe_dest(root: Path, member: str) -> Path:
    """Resolve *member* under *root*, rejecting zip-slip paths."""
    normalized = _normalize_member(member)
    if not normalized or normalized.endswith("/"):
        raise ProjectFormatError(f"Illegal archive path: {member!r}.")
    if normalized.startswith("/") or any(
        part in ("", "..") for part in normalized.split("/")
    ):
        raise ProjectFormatError(f"Illegal archive path: {member!r}.")
    dest = (root / Path(*normalized.split("/"))).resolve()
    if not dest.is_relative_to(root.resolve()):
        raise ProjectFormatError(f"Illegal archive path: {member!r}.")
    return dest
