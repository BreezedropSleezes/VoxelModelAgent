"""In-memory voxel volume with RGBA occupancy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

RGBA = tuple[int, int, int, int]


@dataclass
class VoxelVolume:
    """Dense XYZ volume; voxels[x, y, z] = (r, g, b, a). a==0 means empty."""

    voxels: np.ndarray  # uint8, shape (sx, sy, sz, 4)
    meta: dict = field(default_factory=dict)

    @classmethod
    def empty(cls, size: tuple[int, int, int], meta: dict | None = None) -> "VoxelVolume":
        sx, sy, sz = size
        return cls(voxels=np.zeros((sx, sy, sz, 4), dtype=np.uint8), meta=meta or {})

    @property
    def size(self) -> tuple[int, int, int]:
        sx, sy, sz, _ = self.voxels.shape
        return sx, sy, sz

    def set(self, x: int, y: int, z: int, rgba: RGBA) -> None:
        self.voxels[x, y, z] = rgba

    def fill_box(
        self,
        x0: int,
        y0: int,
        z0: int,
        x1: int,
        y1: int,
        z1: int,
        rgba: RGBA,
        *,
        hollow: bool = False,
        thickness: int = 1,
    ) -> None:
        """Inclusive-exclusive box fill [x0:x1, y0:y1, z0:z1]."""
        sx, sy, sz = self.size
        x0, y0, z0 = max(0, x0), max(0, y0), max(0, z0)
        x1, y1, z1 = min(sx, x1), min(sy, y1), min(sz, z1)
        if x0 >= x1 or y0 >= y1 or z0 >= z1:
            return
        if not hollow:
            self.voxels[x0:x1, y0:y1, z0:z1] = rgba
            return
        t = max(1, thickness)
        self.voxels[x0:x1, y0:y1, z0 : z0 + t] = rgba
        self.voxels[x0:x1, y0:y1, max(z0, z1 - t) : z1] = rgba
        self.voxels[x0:x1, y0 : y0 + t, z0:z1] = rgba
        self.voxels[x0:x1, max(y0, y1 - t) : y1, z0:z1] = rgba
        self.voxels[x0 : x0 + t, y0:y1, z0:z1] = rgba
        self.voxels[max(x0, x1 - t) : x1, y0:y1, z0:z1] = rgba

    def fill_ellipsoid(self, cx: float, cy: float, cz: float, rx: float, ry: float, rz: float, rgba: RGBA) -> None:
        sx, sy, sz = self.size
        x0, x1 = max(0, int(cx - rx)), min(sx, int(cx + rx) + 1)
        y0, y1 = max(0, int(cy - ry)), min(sy, int(cy + ry) + 1)
        z0, z1 = max(0, int(cz - rz)), min(sz, int(cz + rz) + 1)
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    dx = (x + 0.5 - cx) / max(rx, 1e-6)
                    dy = (y + 0.5 - cy) / max(ry, 1e-6)
                    dz = (z + 0.5 - cz) / max(rz, 1e-6)
                    if dx * dx + dy * dy + dz * dz <= 1.0:
                        self.voxels[x, y, z] = rgba

    def occupied_mask(self) -> np.ndarray:
        return self.voxels[..., 3] > 0

    def count_filled(self) -> int:
        return int(np.count_nonzero(self.occupied_mask()))

    def iter_filled(self) -> Iterable[tuple[int, int, int, RGBA]]:
        xs, ys, zs = np.nonzero(self.occupied_mask())
        for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            r, g, b, a = (int(v) for v in self.voxels[x, y, z])
            yield x, y, z, (r, g, b, a)

    def unique_colors(self) -> list[RGBA]:
        mask = self.occupied_mask()
        if not np.any(mask):
            return []
        cols = self.voxels[mask]
        uniq = np.unique(cols, axis=0)
        return [tuple(int(v) for v in row) for row in uniq]  # type: ignore[misc]

    def clone(self) -> "VoxelVolume":
        return VoxelVolume(voxels=self.voxels.copy(), meta=dict(self.meta))
