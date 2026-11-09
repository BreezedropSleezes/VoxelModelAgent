"""Multi-format exporters."""

from __future__ import annotations

import json
from pathlib import Path

from svox.job import JobSpec
from svox.volume import VoxelVolume

from . import glb as glb_mod
from . import qb as qb_mod
from . import vox as vox_mod


def export_all(vol: VoxelVolume, job: JobSpec, out_dir: str | Path) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = job.id
    written: dict[str, Path] = {}

    for fmt in job.export.formats:
        if fmt == "vox":
            path = out_dir / f"{stem}.vox"
            vox_mod.write_vox(vol, path)
            written["vox"] = path
        elif fmt == "qb":
            path = out_dir / f"{stem}.qb"
            qb_mod.write_qb(vol, path, name=stem[:32])
            written["qb"] = path
        elif fmt in {"glb", "gltf"}:
            path = out_dir / f"{stem}.glb"
            glb_mod.write_glb(vol, path)
            written["glb"] = path
        else:
            raise ValueError(f"unsupported format: {fmt}")

    meta_path = out_dir / f"{stem}.job.json"
    meta_path.write_text(json.dumps({"job": job.to_dict(), "volume_meta": vol.meta}, indent=2), encoding="utf-8")
    written["meta"] = meta_path
    return written
