"""Minimal binary glTF (.glb) exporter — one cube mesh instanced per voxel color group."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from svox.volume import VoxelVolume


def _align4(n: int) -> int:
    return (n + 3) & ~3


def _pad4(data: bytes) -> bytes:
    return data + (b"\x00" * (_align4(len(data)) - len(data)))


def write_glb(vol: VoxelVolume, path: str | Path) -> None:
    """
    Build a simple GLB: unit cubes translated to each filled voxel.
    No external deps — hand-rolled glTF 2.0 binary.
    """
    # Unit cube geometry
    positions = [
        0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0,  # z=0
        0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1,  # z=1
    ]
    # 12 triangles
    indices = [
        0, 1, 2, 0, 2, 3,  # back
        4, 6, 5, 4, 7, 6,  # front
        0, 4, 5, 0, 5, 1,  # bottom
        3, 2, 6, 3, 6, 7,  # top
        0, 3, 7, 0, 7, 4,  # left
        1, 5, 6, 1, 6, 2,  # right
    ]

    # Group voxels by color for separate materials/nodes (cap instances for huge volumes)
    by_color: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for x, y, z, rgba in vol.iter_filled():
        by_color.setdefault((rgba[0], rgba[1], rgba[2]), []).append((x, y, z))

    # Flatten all instance translations into one mesh with duplicated cubes (simpler GLB)
    all_pos: list[float] = []
    all_idx: list[int] = []
    all_col: list[float] = []
    base = 0
    count = 0
    max_voxels = 8000
    for (r, g, b), cells in by_color.items():
        cr, cg, cb = r / 255.0, g / 255.0, b / 255.0
        for x, y, z in cells:
            if count >= max_voxels:
                break
            for i in range(0, len(positions), 3):
                all_pos.extend([positions[i] + x, positions[i + 1] + y, positions[i + 2] + z])
                all_col.extend([cr, cg, cb])
            for idx in indices:
                all_idx.append(base + idx)
            base += 8
            count += 1
        if count >= max_voxels:
            break

    if not all_pos:
        # empty mesh placeholder
        all_pos = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        all_col = [1.0, 0.0, 1.0] * 3
        all_idx = [0, 1, 2]

    pos_bytes = b"".join(struct.pack("<f", f) for f in all_pos)
    col_bytes = b"".join(struct.pack("<f", f) for f in all_col)
    # indices as ushort or uint
    if base < 65536:
        idx_bytes = b"".join(struct.pack("<H", i) for i in all_idx)
        idx_ctype = 5123  # UNSIGNED_SHORT
    else:
        idx_bytes = b"".join(struct.pack("<I", i) for i in all_idx)
        idx_ctype = 5125

    # buffer layout: indices | positions | colors (each 4-aligned)
    idx_bytes = _pad4(idx_bytes)
    pos_bytes = _pad4(pos_bytes)
    col_bytes = _pad4(col_bytes)
    bin_chunk = idx_bytes + pos_bytes + col_bytes

    pos_offset = len(idx_bytes)
    col_offset = pos_offset + len(pos_bytes)
    n_verts = len(all_pos) // 3
    n_idx = len(all_idx)

    # min/max for position accessor
    xs = all_pos[0::3]
    ys = all_pos[1::3]
    zs = all_pos[2::3]
    pos_min = [min(xs), min(ys), min(zs)]
    pos_max = [max(xs), max(ys), max(zs)]

    gltf = {
        "asset": {"version": "2.0", "generator": "svox-mvp"},
        "buffers": [{"byteLength": len(bin_chunk)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(idx_bytes) - (len(idx_bytes) - n_idx * (2 if idx_ctype == 5123 else 4)), "target": 34963},
            {"buffer": 0, "byteOffset": pos_offset, "byteLength": n_verts * 12, "target": 34962},
            {"buffer": 0, "byteOffset": col_offset, "byteLength": n_verts * 12, "target": 34962},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": idx_ctype,
                "count": n_idx,
                "type": "SCALAR",
                "max": [n_verts - 1],
                "min": [0],
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": n_verts,
                "type": "VEC3",
                "max": pos_max,
                "min": pos_min,
            },
            {
                "bufferView": 2,
                "componentType": 5126,
                "count": n_verts,
                "type": "VEC3",
            },
        ],
        "materials": [
            {
                "name": "vertex-color",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1, 1, 1, 1],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 1.0,
                },
                "extra": {"note": "colors via COLOR_0"},
            }
        ],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 1, "COLOR_0": 2},
                        "indices": 0,
                        "mode": 4,
                        "material": 0,
                    }
                ]
            }
        ],
        "nodes": [{"mesh": 0, "name": "voxels"}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }

    # Fix bufferView0 byteLength to exact index payload (unpadded logical length)
    idx_logical = n_idx * (2 if idx_ctype == 5123 else 4)
    gltf["bufferViews"][0]["byteLength"] = idx_logical

    json_bytes = _pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"))
    # GLB chunks must be 4-byte aligned; JSON chunk padded with spaces
    json_pad = _align4(len(json_bytes)) - len(json_bytes)
    # already padded with NUL via _pad4; glTF prefers 0x20 spaces for JSON chunk
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes = json_bytes + (b" " * (_align4(len(json_bytes)) - len(json_bytes)))

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_chunk)
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    json_chunk = struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes
    bin_chunk_full = struct.pack("<I4s", len(bin_chunk), b"BIN\x00") + bin_chunk

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + json_chunk + bin_chunk_full)
