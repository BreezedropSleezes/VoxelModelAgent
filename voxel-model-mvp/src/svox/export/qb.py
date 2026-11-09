"""Qubicle Binary (.qb) writer — uncompressed, RGBA, Z-up matrix."""

from __future__ import annotations

import struct
from pathlib import Path

from svox.volume import VoxelVolume


def write_qb(vol: VoxelVolume, path: str | Path, name: str = "Object") -> None:
    """
    QB layout matching Stonehearth-style refs we inspected:
      version=0x0101, colorFormat=0 (RGBA), zAxisOrientation=1,
      compressed=0, visibilityMaskEncoded=1, numMatrices=1
      name as uint8 length + ascii; size uint32×3; pos int32×3; then RGBA voxels in X,Y,Z order.
    """
    sx, sy, sz = vol.size
    # Internal Y-up → QB often uses Z as up; write size as (sx, sz, sy) and remap
    # To stay simple and match game props (~10³), emit matrix as internal (x,y,z) directly
    # with zAxisOrientation=1 meaning Z is vertical in some tools; we map internal y → QB z.
    out_x, out_y, out_z = sx, sz, sy

    name_bytes = name.encode("ascii", "replace")[:255]
    parts: list[bytes] = []
    parts.append(
        struct.pack(
            "<6I",
            0x0101,  # version
            0,  # RGBA
            1,  # z axis orientation
            0,  # uncompressed
            1,  # visibility mask encoded
            1,  # one matrix
        )
    )
    parts.append(bytes([len(name_bytes)]) + name_bytes)
    parts.append(struct.pack("<3I", out_x, out_y, out_z))
    parts.append(struct.pack("<3i", 0, 0, 0))

    # Voxel order for QB: for z in Z, for y in Y, for x in X (common) — actually
    # Qubicle uncompressed is x rightmost nested: for z, for y, for x
    voxel_blob = bytearray()
    for z in range(out_z):  # QB Z = internal Y
        for y in range(out_y):  # QB Y = internal Z
            for x in range(out_x):  # QB X = internal X
                r, g, b, a = (int(v) for v in vol.voxels[x, z, y])
                if a == 0:
                    voxel_blob.extend((0, 0, 0, 0))
                else:
                    # visibility bit in alpha high bit when visibilityMaskEncoded=1
                    vis_a = 255 if a else 0
                    voxel_blob.extend((r, g, b, vis_a))

    parts.append(bytes(voxel_blob))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(parts))
