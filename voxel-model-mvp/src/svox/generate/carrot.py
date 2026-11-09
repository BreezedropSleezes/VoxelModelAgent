"""Procedural carrot with leafy top (food/plant prop)."""

from __future__ import annotations

import random

from svox.job import JobSpec
from svox.volume import RGBA, VoxelVolume


def _pick(palette: list[tuple[int, int, int]] | None, idx: int, fallback: tuple[int, int, int]) -> RGBA:
    if palette and idx < len(palette):
        r, g, b = palette[idx]
        return r, g, b, 255
    r, g, b = fallback
    return r, g, b, 255


def generate(job: JobSpec, rng: random.Random) -> VoxelVolume:
    sx, sy, sz = job.params.size
    vol = VoxelVolume.empty((sx, sy, sz))
    pal = job.params.palette

    orange = _pick(pal, 0, (232, 120, 40))
    orange_dark = _pick(pal, 1, (210, 90, 28))
    leaf = _pick(pal, 2, (70, 140, 55))
    leaf_dark = _pick(pal, 3, (45, 110, 40))

    # Root body: tapered ellipsoid along Y (up)
    body_h = max(6, int(sy * 0.65))
    cx, cz = (sx - 1) / 2.0, (sz - 1) / 2.0
    base_y = 1
    for y in range(base_y, base_y + body_h):
        t = (y - base_y) / max(1, body_h - 1)
        # fat near top of root, taper to tip at bottom... actually carrot tip at bottom
        radius = (0.35 + 0.55 * (1.0 - t)) * min(sx, sz) * 0.42
        radius *= 0.92 + 0.08 * rng.random()
        color = orange if (y + rng.randint(0, 2)) % 3 else orange_dark
        vol.fill_ellipsoid(cx, y, cz, radius, 0.6, radius, color)

    # Leafy greens on top
    leaf_base = base_y + body_h - 1
    for i in range(5):
        angle = i / 5.0
        ox = int(round((sx - 1) / 2 + (1.5 + rng.random()) * (1 if i % 2 == 0 else -1) * (0.5 + angle)))
        oz = int(round((sz - 1) / 2 + (1.2 + rng.random()) * (1 if i % 3 else -1)))
        height = 2 + rng.randint(1, max(1, sy - leaf_base - 2))
        for h in range(height):
            y = leaf_base + h
            if not (0 <= ox < sx and 0 <= y < sy and 0 <= oz < sz):
                continue
            c = leaf if h % 2 == 0 else leaf_dark
            vol.set(ox, y, oz, c)
            if h > 0 and rng.random() < 0.5:
                nx = min(sx - 1, max(0, ox + rng.choice([-1, 1])))
                vol.set(nx, y, oz, c)

    vol.meta["parts"] = ["root", "leaves"]
    return vol
