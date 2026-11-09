"""Style constraints: palette quantize, denoise, blockiness."""

from __future__ import annotations

from collections import Counter

import numpy as np

from svox.job import JobSpec
from svox.volume import RGBA, VoxelVolume


def _quantize_color(rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    best = palette[0]
    best_d = 1e18
    r, g, b = rgb
    for pr, pg, pb in palette:
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best_d = d
            best = (pr, pg, pb)
    return best


def _remove_lonely(vol: VoxelVolume, min_neighbors: int = 1) -> int:
    """Clear voxels with too few occupied 6-neighbors (pepper noise)."""
    mask = vol.occupied_mask()
    sx, sy, sz = vol.size
    removed = 0
    # single pass is enough for MVP
    coords = list(zip(*np.nonzero(mask)))
    for x, y, z in coords:
        n = 0
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nx, ny, nz = x + dx, y + dy, z + dz
            if 0 <= nx < sx and 0 <= ny < sy and 0 <= nz < sz and mask[nx, ny, nz]:
                n += 1
        if n < min_neighbors:
            vol.voxels[x, y, z] = (0, 0, 0, 0)
            removed += 1
    return removed


def stylize(vol: VoxelVolume, job: JobSpec) -> VoxelVolume:
    out = vol.clone()
    palette = job.params.palette or [(128, 128, 128)]
    # Quantize occupied voxels to job palette (theme/asset colors — not a global warm-earth map)
    xs, ys, zs = np.nonzero(out.occupied_mask())
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        r, g, b, a = (int(v) for v in out.voxels[x, y, z])
        qr, qg, qb = _quantize_color((r, g, b), palette)
        out.voxels[x, y, z] = (qr, qg, qb, a)

    removed = _remove_lonely(out, min_neighbors=1)
    # Drop tiny components? skip for MVP if volume already small

    counts: Counter[RGBA] = Counter()
    for *_, rgba in out.iter_filled():
        counts[rgba] += 1

    out.meta = dict(vol.meta)
    out.meta.update(
        {
            "stylize": {
                "palette_size": len(palette),
                "removed_lonely": removed,
                "filled": out.count_filled(),
                "unique_colors": len(counts),
            }
        }
    )
    return out
