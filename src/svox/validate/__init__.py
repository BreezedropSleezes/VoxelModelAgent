"""Validation gates for generated volumes / exports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from svox.job import JobSpec
from svox.volume import VoxelVolume


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise SystemExit("validate failed:\n- " + "\n- ".join(self.errors))


def validate(vol: VoxelVolume, job: JobSpec, written: dict[str, Path] | None = None) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    filled = vol.count_filled()
    if filled <= 0:
        errors.append("volume is empty")

    sx, sy, sz = vol.size
    if max(sx, sy, sz) > 64:
        errors.append(f"axis exceeds hard cap 64: {(sx, sy, sz)}")

    total = sx * sy * sz
    occupancy = filled / total if total else 0.0
    if occupancy > 0.95:
        warnings.append(f"very high occupancy {occupancy:.2%}")
    if occupancy < 0.001 and filled > 0:
        warnings.append(f"very sparse occupancy {occupancy:.2%}")

    if job.params.theme in {"cottage", "house", "tavern", "building"}:
        errors.append("building theme leaked into validate")

    if written:
        for key, path in written.items():
            if key == "meta":
                continue
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"export {key} missing or empty: {path}")

        vox = written.get("vox")
        if vox and vox.exists():
            data = vox.read_bytes()
            if not data.startswith(b"VOX "):
                errors.append("vox magic mismatch")

    ok = not errors
    return ValidationReport(ok=ok, errors=errors, warnings=warnings)
