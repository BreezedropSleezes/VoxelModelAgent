"""Procedural wooden crate / prop box."""

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

    wood = _pick(pal, 0, (139, 90, 43))
    wood_dark = _pick(pal, 1, (101, 67, 33))
    wood_light = _pick(pal, 2, (160, 120, 70))
    iron = _pick(pal, 3, (70, 70, 75))

    # Inset hollow box
    margin = 1 if min(sx, sy, sz) >= 8 else 0
    x0, y0, z0 = margin, margin, margin
    x1, y1, z1 = sx - margin, sy - margin, sz - margin
    vol.fill_box(x0, y0, z0, x1, y1, z1, wood, hollow=True, thickness=1)

    # Floor planks
    for x in range(x0 + 1, x1 - 1):
        for z in range(z0 + 1, z1 - 1):
            vol.set(x, y0, z, wood_dark if (x + z) % 2 else wood)

    # Vertical corner posts
    for x, z in ((x0, z0), (x0, z1 - 1), (x1 - 1, z0), (x1 - 1, z1 - 1)):
        for y in range(y0, y1):
            vol.set(x, y, z, wood_dark)

    # Horizontal strap bands (iron)
    band_ys = {y0 + 1, (y0 + y1) // 2, y1 - 2}
    for y in band_ys:
        if y0 < y < y1:
            for x in range(x0, x1):
                vol.set(x, y, z0, iron)
                vol.set(x, y, z1 - 1, iron)
            for z in range(z0, z1):
                vol.set(x0, y, z, iron)
                vol.set(x1 - 1, y, z, iron)

    # Lid planks on top
    for x in range(x0, x1):
        for z in range(z0, z1):
            if rng.random() < 0.15:
                continue
            vol.set(x, y1 - 1, z, wood_light if (x % 3) else wood)

    vol.meta["parts"] = ["box", "straps", "lid"]
    return vol
