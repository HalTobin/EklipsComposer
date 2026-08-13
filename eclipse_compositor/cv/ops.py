"""Lightweight NumPy / Pillow stand-ins for the OpenCV calls this app uses.

Avoids bundling the ~100 MB ``cv2`` wheel (ffmpeg, tesseract, video codecs)
while keeping disc detection and I/O behaviour close to the previous pipeline.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image

# OpenCV MORPH_ELLIPSE 5×5 (inscribed ellipse, r=2).
_ELLIPSE_5 = np.array(
    [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
        [0, 1, 1, 1, 0],
        [0, 0, 1, 0, 0],
    ],
    dtype=np.uint8,
)

# OpenCV GaussianBlur 5×5 with sigma=0 → σ = 0.3*((k-1)*0.5-1)+0.8 = 1.1
_GAUSS_5 = np.array([0.067907, 0.239257, 0.385672, 0.239257, 0.067907], dtype=np.float64)


def bgr_to_gray(image: np.ndarray) -> np.ndarray:
    """Convert a BGR uint8 image to grayscale (BT.601, OpenCV weights)."""
    if image.ndim == 2:
        return image
    bgr = image.astype(np.float32)
    gray = 0.114 * bgr[:, :, 0] + 0.587 * bgr[:, :, 1] + 0.299 * bgr[:, :, 2]
    return np.clip(gray, 0, 255).astype(np.uint8)


def gaussian_blur_5(image: np.ndarray) -> np.ndarray:
    """Separable 5-tap Gaussian blur matching OpenCV's 5×5 σ=0 kernel."""
    pad = 2
    src = image.astype(np.float64)
    padded = np.pad(src, ((0, 0), (pad, pad)), mode="edge")
    horiz = np.zeros_like(src)
    for i, k in enumerate(_GAUSS_5):
        horiz += k * padded[:, i : i + src.shape[1]]
    padded = np.pad(horiz, ((pad, pad), (0, 0)), mode="edge")
    vert = np.zeros_like(src)
    for i, k in enumerate(_GAUSS_5):
        vert += k * padded[i : i + src.shape[0], :]
    return np.clip(np.rint(vert), 0, 255).astype(np.uint8)


def threshold_binary(image: np.ndarray, threshold: int, invert: bool) -> np.ndarray:
    """Binary threshold to 0/255, matching ``cv2.THRESH_BINARY[_INV]``."""
    if invert:
        return np.where(image <= threshold, 255, 0).astype(np.uint8)
    return np.where(image > threshold, 255, 0).astype(np.uint8)


def _morph(mask: np.ndarray, op: str) -> np.ndarray:
    """Binary dilate or erode with the 5×5 ellipse kernel."""
    binary = mask > 0
    pad_y, pad_x = 2, 2
    padded = np.pad(binary, ((pad_y, pad_y), (pad_x, pad_x)), mode="constant")
    windows = sliding_window_view(padded, _ELLIPSE_5.shape)
    ky, kx = np.nonzero(_ELLIPSE_5)
    selected = windows[:, :, ky, kx]
    out = selected.any(axis=-1) if op == "dilate" else selected.all(axis=-1)
    return out.astype(np.uint8) * 255


def morph_open_close(mask: np.ndarray) -> np.ndarray:
    """Open then close with a 5×5 ellipse (same cleanup as the old cv2 path)."""
    opened = _morph(_morph(mask, "erode"), "dilate")
    return _morph(_morph(opened, "dilate"), "erode")


def _label_8(binary: np.ndarray) -> tuple[np.ndarray, int]:
    """Two-pass 8-connected labels. *binary* is a small bool array."""
    h, w = binary.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parent = [0]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    next_label = 1
    for y in range(h):
        row = binary[y]
        prev = labels[y - 1] if y else None
        for x in range(w):
            if not row[x]:
                continue
            neigh: list[int] = []
            if x and labels[y, x - 1]:
                neigh.append(int(labels[y, x - 1]))
            if prev is not None:
                if labels[y - 1, x]:
                    neigh.append(int(labels[y - 1, x]))
                if x and labels[y - 1, x - 1]:
                    neigh.append(int(labels[y - 1, x - 1]))
                if x + 1 < w and labels[y - 1, x + 1]:
                    neigh.append(int(labels[y - 1, x + 1]))
            if not neigh:
                parent.append(next_label)
                labels[y, x] = next_label
                next_label += 1
                continue
            m = min(neigh)
            labels[y, x] = m
            for n in neigh:
                ra, rb = find(m), find(n)
                if ra != rb:
                    parent[ra] = rb

    remap: dict[int, int] = {}
    current = 0
    flat = labels.ravel()
    for i, lab in enumerate(flat):
        if lab == 0:
            continue
        root = find(int(lab))
        rid = remap.get(root)
        if rid is None:
            current += 1
            remap[root] = current
            rid = current
        flat[i] = rid
    return labels, current


def _largest_roi(binary: np.ndarray) -> tuple[slice, slice] | None:
    """BBox of the largest 8-connected blob, from a coarse label pass."""
    h, w = binary.shape
    stride = 4 if max(h, w) > 800 else 2 if max(h, w) > 400 else 1
    small = binary[::stride, ::stride]
    if not small.any():
        return None
    labels, n = _label_8(small)
    if n == 0:
        return None
    counts = np.bincount(labels.ravel())
    counts[0] = 0
    lab = int(counts.argmax())
    ys, xs = np.nonzero(labels == lab)
    margin = max(stride, 2)
    y0 = max(0, int(ys.min()) * stride - margin)
    x0 = max(0, int(xs.min()) * stride - margin)
    y1 = min(h, (int(ys.max()) + 1) * stride + margin)
    x1 = min(w, (int(xs.max()) + 1) * stride + margin)
    return slice(y0, y1), slice(x0, x1)


def _convex_hull(points: np.ndarray) -> np.ndarray:
    """Andrew's monotone chain. *points* is (N, 2) float ``(x, y)``."""
    pts = np.unique(points, axis=0)
    if len(pts) <= 2:
        return pts

    def cross(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
        return float((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]))

    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    lower: list[np.ndarray] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[np.ndarray] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1], dtype=np.float64)
    return hull if len(hull) else pts


def _polygon_area_centroid(hull: np.ndarray) -> tuple[float, float, float]:
    """Shoelace area and centroid of a closed convex polygon."""
    if len(hull) == 0:
        return 0.0, 0.0, 0.0
    if len(hull) == 1:
        return 1.0, float(hull[0, 0]), float(hull[0, 1])
    if len(hull) == 2:
        return float(np.linalg.norm(hull[1] - hull[0])), float(hull[:, 0].mean()), float(
            hull[:, 1].mean()
        )
    x, y = hull[:, 0], hull[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y2 - x2 * y
    area = 0.5 * float(np.sum(cross))
    if abs(area) < 1e-9:
        return 0.0, float(x.mean()), float(y.mean())
    cx = float(np.sum((x + x2) * cross) / (6.0 * area))
    cy = float(np.sum((y + y2) * cross) / (6.0 * area))
    return abs(area), cx, cy


def _circle_from(points: list[tuple[float, float]]) -> tuple[tuple[float, float], float]:
    """Smallest circle through 0–3 points."""
    if not points:
        return (0.0, 0.0), 0.0
    if len(points) == 1:
        return points[0], 0.0
    if len(points) == 2:
        (x1, y1), (x2, y2) = points
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0), math.hypot(x1 - x2, y1 - y2) / 2.0
    (x1, y1), (x2, y2), (x3, y3) = points[:3]
    d = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        pairs = (
            (points[0], points[1]),
            (points[0], points[2]),
            (points[1], points[2]),
        )
        return max((_circle_from([a, b]) for a, b in pairs), key=lambda c: c[1])
    ux = (
        (x1 * x1 + y1 * y1) * (y2 - y3)
        + (x2 * x2 + y2 * y2) * (y3 - y1)
        + (x3 * x3 + y3 * y3) * (y1 - y2)
    ) / d
    uy = (
        (x1 * x1 + y1 * y1) * (x3 - x2)
        + (x2 * x2 + y2 * y2) * (x1 - x3)
        + (x3 * x3 + y3 * y3) * (x2 - x1)
    ) / d
    return (ux, uy), math.hypot(x1 - ux, y1 - uy)


def min_enclosing_circle(points: np.ndarray) -> tuple[tuple[float, float], float]:
    """Welzl's algorithm on a small point set (convex-hull vertices)."""
    pts = [(float(x), float(y)) for x, y in points]
    rng = random.Random(0)
    rng.shuffle(pts)

    def inside(
        circle: tuple[tuple[float, float], float],
        p: tuple[float, float],
    ) -> bool:
        (cx, cy), r = circle
        return math.hypot(p[0] - cx, p[1] - cy) <= r + 1e-6

    def rec(
        idx: int,
        boundary: list[tuple[float, float]],
    ) -> tuple[tuple[float, float], float]:
        if idx == len(pts) or len(boundary) == 3:
            return _circle_from(boundary)
        circle = rec(idx + 1, boundary)
        if inside(circle, pts[idx]):
            return circle
        return rec(idx + 1, boundary + [pts[idx]])

    if not pts:
        return (0.0, 0.0), 0.0
    return rec(0, [])


def largest_blob_geometry(
    mask: np.ndarray,
) -> tuple[np.ndarray, float] | None:
    """Convex hull and pixel area of the largest 8-connected foreground blob.

    Args:
        mask: Binary 0/255 (or 0/1) image.

    Returns:
        ``(hull_xy, area)`` where *hull_xy* is ``(N, 2)`` float, or ``None``.
    """
    binary = mask > 0
    if not binary.any():
        return None
    roi_slices = _largest_roi(binary)
    if roi_slices is None:
        return None
    ys, xs = roi_slices
    roi = binary[ys, xs]
    if not roi.any():
        return None
    area = float(roi.sum())
    # Silhouette: leftmost + rightmost foreground pixel per row (solid blob).
    row_has = roi.any(axis=1)
    if not row_has.any():
        return None
    left = np.argmax(roi, axis=1)
    right = roi.shape[1] - 1 - np.argmax(roi[:, ::-1], axis=1)
    yy = np.nonzero(row_has)[0]
    origin_x = xs.start or 0
    origin_y = ys.start or 0
    pts_left = np.column_stack((left[row_has] + origin_x, yy + origin_y))
    pts_right = np.column_stack((right[row_has] + origin_x, yy + origin_y))
    points = np.vstack((pts_left, pts_right)).astype(np.float64)
    hull = _convex_hull(points)
    if len(hull) == 0:
        return None
    return hull, area


def hull_perimeter(hull: np.ndarray) -> float:
    """Closed-polygon perimeter of *hull* vertices."""
    if len(hull) < 2:
        return 0.0
    rolled = np.roll(hull, -1, axis=0)
    return float(np.sum(np.linalg.norm(rolled - hull, axis=1)))


def resize_hw(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize *image* to ``(height, width)`` with area-like downscale."""
    if image.shape[1] == width and image.shape[0] == height:
        return image
    src = Image.fromarray(image)
    down = width < image.shape[1] or height < image.shape[0]
    resample = Image.Resampling.BOX if down else Image.Resampling.BICUBIC
    return np.asarray(src.resize((width, height), resample))


def load_bgr(path: Path | str) -> np.ndarray:
    """Load an image as BGR uint8, matching ``cv2.imread(..., IMREAD_COLOR)``.

    EXIF orientation is ignored, same as OpenCV.
    """
    path = Path(path)
    with Image.open(path) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
    return rgb[:, :, ::-1].copy()


def save_bgr(path: Path | str, image: np.ndarray, jpeg_quality: int = 95) -> None:
    """Write a BGR uint8 image; format is inferred from the suffix."""
    path = Path(path)
    rgb = image[:, :, ::-1] if image.ndim == 3 else image
    im = Image.fromarray(rgb)
    ext = path.suffix.lower()
    kwargs: dict = {}
    if ext in {".jpg", ".jpeg"}:
        kwargs = {"quality": jpeg_quality, "subsampling": 0}
    elif ext in {".tif", ".tiff"}:
        kwargs = {"compression": "raw"}
    im.save(path, **kwargs)


# Re-export shoelace helpers used by detection.
polygon_area_centroid = _polygon_area_centroid
