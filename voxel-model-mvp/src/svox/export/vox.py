"""MagicaVoxel .vox writer (MAIN/SIZE/XYZI/RGBA)."""

from __future__ import annotations

import struct
from pathlib import Path

from svox.volume import VoxelVolume


def _chunk(chunk_id: bytes, content: bytes, children: bytes = b"") -> bytes:
    return chunk_id + struct.pack("<II", len(content), len(children)) + content + children


def write_vox(vol: VoxelVolume, path: str | Path) -> None:
    sx, sy, sz = vol.size
    # Internal Y-up (x, y, z) → MagicaVoxel (x, y_depth=z, z_up=y)
    size_content = struct.pack("<III", sx, sz, sy)

    color_to_index: dict[tuple[int, int, int, int], int] = {}
    # palette[0] unused; indices 1..255 used by XYZI
    palette: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)] * 256
    next_idx = 1

    voxels_xyz: list[tuple[int, int, int, int]] = []
    for x, y, z, rgba in vol.iter_filled():
        if rgba not in color_to_index:
            idx = min(next_idx, 255)
            color_to_index[rgba] = idx
            if next_idx <= 255:
                r, g, b, a = rgba
                palette[next_idx] = (r, g, b, a if a else 255)
                next_idx += 1
        voxels_xyz.append((x, z, y, color_to_index[rgba]))

    xyzi = struct.pack("<I", len(voxels_xyz))
    for x, y, z, idx in voxels_xyz:
        xyzi += struct.pack("<BBBB", x & 0xFF, y & 0xFF, z & 0xFF, idx & 0xFF)

    # 256 RGBA entries for palette indices 1..255 (+ one trailing unused slot)
    rgba_content = b"".join(struct.pack("<BBBB", *palette[i]) for i in range(1, 256))
    rgba_content += struct.pack("<BBBB", 0, 0, 0, 0)

    children = _chunk(b"SIZE", size_content) + _chunk(b"XYZI", xyzi) + _chunk(b"RGBA", rgba_content)
    main = _chunk(b"MAIN", b"", children)
    data = b"VOX " + struct.pack("<I", 150) + main

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
