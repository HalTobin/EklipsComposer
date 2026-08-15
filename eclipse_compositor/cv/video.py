"""Video probing and frame extraction via ffmpeg.

A decode-only ffmpeg is bundled with the packaged app. Local development
uses ``EKLIPSCOMPOSER_FFMPEG``, ``PATH``, or an optional ``imageio-ffmpeg``
install.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from eclipse_compositor.cv.ops import save_bgr

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".mpg", ".mpeg"}
)

_DURATION_RE = re.compile(
    r"Duration:\s*(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)"
)
_FPS_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*fps")
_TBR_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*tbr")
_NB_FRAMES_RE = re.compile(
    r"(?:NUMBER_OF_FRAMES|nb_frames|nframes)\s*[:=]\s*(\d+)",
    re.IGNORECASE,
)
_VIDEO_STREAM_RE = re.compile(r"Stream\s+#.*Video:", re.IGNORECASE)
_SIZE_RE = re.compile(r"(\d{2,5})x(\d{2,5})")


@dataclass(frozen=True)
class VideoProbe:
    """Lightweight metadata used to confirm a video import."""

    path: Path
    frame_count: int | None
    fps: float
    duration: float
    size: tuple[int, int] | None = None


def is_supported_video(path: Path | str) -> bool:
    """Return True if *path* has a supported video suffix."""
    return Path(path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def video_dialog_globs() -> str:
    """Qt file-dialog glob list for supported video suffixes."""
    return " ".join(f"*{ext}" for ext in sorted(SUPPORTED_VIDEO_EXTENSIONS))


def ffmpeg_exe() -> str:
    """Return the ffmpeg binary used for video import.

    Search order: ``EKLIPSCOMPOSER_FFMPEG``, bundled next to a frozen app,
    repo ``third_party/ffmpeg``, ``PATH``, optional ``imageio-ffmpeg``.

    Raises:
        FileNotFoundError: If no ffmpeg binary can be located.
    """
    env = os.environ.get("EKLIPSCOMPOSER_FFMPEG")
    if env and Path(env).is_file():
        return env

    names = ("ffmpeg", "ffmpeg.exe")
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        meipass = getattr(sys, "_MEIPASS", None)
        roots = [exe_dir, exe_dir.parent / "Frameworks"]
        if meipass:
            roots.append(Path(meipass))
        for root in roots:
            for name in names:
                candidate = root / name
                if candidate.is_file():
                    return str(candidate)

    repo_bin = Path(__file__).resolve().parents[2] / "third_party" / "ffmpeg" / "ffmpeg"
    if repo_bin.is_file():
        return str(repo_bin)

    which = shutil.which("ffmpeg")
    if which:
        return which

    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and Path(bundled).is_file():
            return bundled
    except Exception:  # noqa: BLE001 — optional local-dev fallback
        pass

    raise FileNotFoundError(
        "ffmpeg is not available to read video files. "
        "Install ffmpeg or build the decode-only binary with "
        "build_scripts/build_ffmpeg.sh."
    )


def probe_video(path: Path | str, *, timeout: float = 20.0) -> VideoProbe:
    """Read duration / fps and estimate how many frames will be imported.

    Uses ``ffmpeg -i`` header output only (no full decode). ``frame_count``
    is taken from container tags when present, otherwise ``round(duration * fps)``.

    Args:
        path: Video file to inspect.
        timeout: Seconds to wait for ffmpeg metadata.

    Returns:
        ``VideoProbe`` with an estimated frame count (or ``None`` if unknown).

    Raises:
        FileNotFoundError: If ffmpeg cannot open a video stream.
        TimeoutError: If ffmpeg does not return within *timeout*.
    """
    path = Path(path)
    exe = ffmpeg_exe()

    try:
        result = subprocess.run(
            [exe, "-hide_banner", "-i", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Timed out reading video metadata: {path.name}") from exc

    text = f"{result.stderr or ''}\n{result.stdout or ''}"
    if not _VIDEO_STREAM_RE.search(text):
        raise FileNotFoundError(f"No video stream found in {path.name}")

    fps = 0.0
    fps_match = _FPS_RE.search(text)
    if fps_match:
        fps = float(fps_match.group(1))
    else:
        tbr_match = _TBR_RE.search(text)
        if tbr_match:
            fps = float(tbr_match.group(1))

    duration = 0.0
    duration_match = _DURATION_RE.search(text)
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    tagged = _NB_FRAMES_RE.search(text)
    if tagged:
        frame_count = int(tagged.group(1))
    elif fps > 0 and duration > 0:
        frame_count = max(1, int(round(duration * fps)))
    else:
        frame_count = None

    size: tuple[int, int] | None = None
    for line in text.splitlines():
        if "Video:" not in line:
            continue
        size_match = _SIZE_RE.search(line)
        if size_match:
            size = (int(size_match.group(1)), int(size_match.group(2)))
            break

    return VideoProbe(
        path=path,
        frame_count=frame_count,
        fps=fps,
        duration=duration,
        size=size,
    )


def stepped_frame_count(total: int, step: int) -> int:
    """How many frames are enabled when checking every *step*-th imported frame.

    Step ``1`` enables every frame. Indices enabled are ``0, step, 2*step, …``.
    """
    if total <= 0:
        return 0
    stride = max(1, int(step))
    return (total - 1) // stride + 1


def iter_extracted_frames(
    path: Path | str,
    output_dir: Path,
    progress: Callable[[int], None] | None = None,
) -> Iterator[tuple[Path, np.ndarray]]:
    """Decode *path*, write JPEG stills into *output_dir*, and yield BGR frames.

    Args:
        path: Source video.
        output_dir: Directory that already exists; JPEG stills are written here.
        progress: Optional callback invoked with the 1-based decoded count.

    Yields:
        ``(still_path, bgr)`` for each decoded frame.
    """
    path = Path(path)
    stem = _safe_stem(path.stem)
    info = probe_video(path)
    if info.size is None:
        raise FileNotFoundError(f"Could not read frame size from {path.name}")
    width, height = info.size
    frame_bytes = width * height * 3
    exe = ffmpeg_exe()
    cmd = [
        exe,
        "-hide_banner",
        "-i",
        str(path),
        "-an",
        "-sn",
        "-pix_fmt",
        "rgb24",
        "-vcodec",
        "rawvideo",
        "-f",
        "rawvideo",
        "-",
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stderr_chunks: list[bytes] = []

    def _drain_stderr() -> None:
        if proc.stderr is None:
            return
        stderr_chunks.append(proc.stderr.read())

    drain = threading.Thread(target=_drain_stderr, daemon=True)
    drain.start()
    stdout = proc.stdout
    if stdout is None:
        proc.kill()
        raise RuntimeError("ffmpeg produced no stdout pipe.")
    try:
        index = 0
        while True:
            raw = _read_exactly(stdout, frame_bytes)
            if raw is None:
                break
            rgb = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
            bgr = np.ascontiguousarray(rgb[:, :, ::-1])
            still = output_dir / f"{stem}_{index:05d}.jpg"
            save_bgr(still, bgr)
            if progress is not None:
                progress(index + 1)
            yield still, bgr
            index += 1
    finally:
        stdout.close()
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        drain.join(timeout=2.0)
    if index == 0:
        err = b"".join(stderr_chunks).decode("utf-8", "replace").strip()
        detail = f"\n{err}" if err else ""
        raise RuntimeError(f"No frames decoded from {path.name}.{detail}")


def _read_exactly(stream: object, size: int) -> bytes | None:
    """Read *size* bytes, or ``None`` on a clean EOF at a frame boundary."""
    chunks: list[bytes] = []
    remaining = size
    read = stream.read  # type: ignore[attr-defined]
    while remaining:
        block = read(remaining)
        if not block:
            if not chunks:
                return None
            raise RuntimeError("ffmpeg ended mid-frame.")
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def _safe_stem(stem: str) -> str:
    """Return a filesystem-friendly stem for extracted frame names."""
    cleaned = re.sub(r"[^\w.\-]+", "_", stem, flags=re.UNICODE).strip("._")
    return cleaned[:80] or "video"
