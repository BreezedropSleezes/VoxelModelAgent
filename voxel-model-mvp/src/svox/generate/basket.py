"""Procedural berry basket placeholder."""

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

    wicker = _pick(pal, 0, (142, 118, 65))
    wicker2 = _pick(pal, 1, (128, 103, 62))
    dark = _pick(pal, 2, (88, 71, 43))
    berry = _pick(pal, 3, (60, 20, 82))
    berry2 = _pick(pal, 4, (97, 47, 127))

    # Basket shell
    vol.fill_box(1, 0, 1, sx - 1, max(2, sy // 2), sz - 1, wicker, hollow=True, thickness=1)
    for x in range(1, sx - 1):
        for z in range(1, sz - 1):
            vol.set(x, 0, z, dark if (x + z) % 2 else wicker2)

    # Handle arc
    cy = min(sy - 1, sy // 2 + 2)
    cx, cz = (sx - 1) / 2.0, (sz - 1) / 2.0
    for i in range(16):
        ang = math.pi * i / 15.0
        x = int(round(cx + math.cos(ang) * (sx / 2 - 1.5)))
        y = int(round(cy + math.sin(ang) * (sy / 2 - 1)))
        z = int(round(cz))
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            vol.set(x, y, z, dark)

    # Berries fill
    fill_top = max(1, sy // 2 - 1)
    for x in range(2, sx - 2):
        for z in range(2, sz - 2):
            for y in range(1, fill_top):
                if rng.random() < 0.55:
                    vol.set(x, y, z, berry if rng.random() < 0.6 else berry2)

    vol.meta["parts"] = ["basket", "handle", "berries"]
    return vol
