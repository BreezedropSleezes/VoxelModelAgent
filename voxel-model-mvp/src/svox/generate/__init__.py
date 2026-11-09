"""Voxel generation strategies."""

from __future__ import annotations

import random
from typing import Callable

from svox.job import JobSpec
from svox.volume import VoxelVolume

from . import basket, carrot, crate, stew

GeneratorFn = Callable[[JobSpec, random.Random], VoxelVolume]

GENERATORS: dict[str, GeneratorFn] = {
    "carrot": carrot.generate,
    "crate": crate.generate,
    "stew": stew.generate,
    "basket": basket.generate,
}


def generate(job: JobSpec) -> VoxelVolume:
    theme = job.params.theme
    fn = GENERATORS.get(theme)
    if fn is None:
        known = ", ".join(sorted(GENERATORS))
        raise ValueError(f"no procedural generator for theme '{theme}' (known: {known})")
    rng = random.Random(job.seed)
    vol = fn(job, rng)
    vol.meta.update(
        {
            "theme": theme,
            "seed": job.seed,
            "generator_backend": "procedural",
            "palette_source": job.params.palette_source,
        }
    )
    return vol
