"""Procedural stew pot placeholder (food prop, Stonehearth-ish scale)."""

from __future__ import annotations

import math
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

    pot = _pick(pal, 0, (106, 103, 94))
    pot_dark = _pick(pal, 1, (88, 86, 78))
    stew = _pick(pal, 2, (58, 104, 49))
    rim = _pick(pal, 3, (138, 133, 123))
    chunk = _pick(pal, 4, (55, 28, 5))

    cx, cz = (sx - 1) / 2.0, (sz - 1) / 2.0
    pot_h = max(5, int(sy * 0.7))
    radius = min(sx, sz) * 0.42

    for y in range(1, pot_h):
        t = y / max(1, pot_h - 1)
        r = radius * (0.75 + 0.25 * math.sin(t * math.pi))
        # outer shell
        for x in range(sx):
            for z in range(sz):
                dx, dz = x + 0.5 - cx, z + 0.5 - cz
                dist = math.hypot(dx, dz)
                if abs(dist - r) <= 0.85:
                    vol.set(x, y, z, pot_dark if y % 2 else pot)
                elif dist < r - 0.85 and y == 1:
                    vol.set(x, y, z, pot_dark)  # bottom

    # stew surface + chunks
    surface_y = pot_h - 2
    for x in range(sx):
        for z in range(sz):
            dx, dz = x + 0.5 - cx, z + 0.5 - cz
            if math.hypot(dx, dz) < radius * 0.72:
                vol.set(x, surface_y, z, stew)
                if rng.random() < 0.12:
                    vol.set(x, surface_y, z, chunk)

    # rim
    for x in range(sx):
        for z in range(sz):
            dx, dz = x + 0.5 - cx, z + 0.5 - cz
            dist = math.hypot(dx, dz)
            if abs(dist - radius * 0.95) <= 0.7:
                vol.set(x, pot_h - 1, z, rim)

    vol.meta["parts"] = ["pot", "stew", "rim"]
    return vol
