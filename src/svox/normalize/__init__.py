"""Input normalization → Job Spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from svox.job import (
    ALLOWED_BACKENDS,
    ALLOWED_CATEGORIES,
    ALLOWED_FORMATS,
    FORBIDDEN_THEMES,
    JobExport,
    JobParams,
    JobSpec,
)

THEME_DEFAULTS: dict[str, dict[str, Any]] = {
    "crate": {
        "category": "prop",
        "size": [16, 16, 16],
        "palette": [[139, 90, 43], [101, 67, 33], [160, 120, 70], [70, 70, 75]],
    },
    "carrot": {
        "category": "plant",
        "size": [12, 20, 12],
        "palette": [[232, 120, 40], [210, 90, 28], [70, 140, 55], [45, 110, 40], [160, 100, 50]],
    },
    "stew": {
        "category": "item",
        "size": [12, 10, 12],
        "palette": [[106, 103, 94], [88, 86, 78], [58, 104, 49], [138, 133, 123], [55, 28, 5]],
    },
    "basket": {
        "category": "prop",
        "size": [12, 10, 12],
        "palette": [[142, 118, 65], [128, 103, 62], [88, 71, 43], [60, 20, 82], [97, 47, 127]],
    },
}


def _as_rgb_list(value: Any) -> list[tuple[int, int, int]] | None:
    if not value:
        return None
    out: list[tuple[int, int, int]] = []
    for item in value:
        if len(item) < 3:
            raise ValueError(f"palette entry needs 3 channels, got {item}")
        out.append((int(item[0]), int(item[1]), int(item[2])))
    return out


def _parse_size(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if value is None:
        return fallback
    if isinstance(value, str):
        parts = [int(p.strip()) for p in value.replace("x", ",").split(",")]
    else:
        parts = [int(p) for p in value]
    if len(parts) != 3:
        raise ValueError(f"size must be 3 ints, got {value}")
    if any(p < 1 or p > 64 for p in parts):
        raise ValueError(f"size axes must be in 1..64, got {parts}")
    return parts[0], parts[1], parts[2]


def load_manifest(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a mapping: {path}")
    return data


def normalize_job(
    *,
    manifest: dict[str, Any] | None = None,
    text: str | None = None,
    theme: str | None = None,
    size: tuple[int, int, int] | str | None = None,
    seed: int | None = None,
    formats: list[str] | None = None,
    backend: str | None = None,
    job_id: str | None = None,
) -> JobSpec:
    """Merge CLI overrides onto a manifest (or defaults) into a JobSpec."""
    raw = dict(manifest or {})
    params_raw = dict(raw.get("params") or {})

    resolved_theme = (theme or params_raw.get("theme") or raw.get("theme") or "carrot").lower()
    if resolved_theme in FORBIDDEN_THEMES:
        raise ValueError(
            f"theme '{resolved_theme}' is architectural/building-scoped and rejected "
            "(pipeline only generates independent props/items/plants/animals)"
        )

    theme_defaults = THEME_DEFAULTS.get(resolved_theme, THEME_DEFAULTS["crate"])
    category = str(params_raw.get("category") or theme_defaults["category"]).lower()
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"category must be one of {sorted(ALLOWED_CATEGORIES)}, got {category}")

    default_size = tuple(theme_defaults["size"])
    resolved_size = _parse_size(size if size is not None else params_raw.get("size"), default_size)  # type: ignore[arg-type]

    resolved_backend = (backend or params_raw.get("backend") or "procedural").lower()
    if resolved_backend not in ALLOWED_BACKENDS:
        raise ValueError(f"backend must be one of {sorted(ALLOWED_BACKENDS)}")
    # MVP: image backends fall back to procedural with a warning flag
    if resolved_backend in {"image_p1", "image_p2", "auto"} and not raw.get("image"):
        resolved_backend = "procedural"

    palette = _as_rgb_list(params_raw.get("palette")) or _as_rgb_list(theme_defaults.get("palette"))

    export_raw = dict(raw.get("export") or {})
    fmt_list = formats or export_raw.get("formats") or ["vox", "qb", "glb"]
    fmt_list = [str(f).lower() for f in fmt_list]
    bad = [f for f in fmt_list if f not in ALLOWED_FORMATS]
    if bad:
        raise ValueError(f"unsupported formats: {bad}")

    image = raw.get("image")
    likeness = bool(raw.get("likeness_required") or bool(image))
    resolved_text = text if text is not None else raw.get("text")
    resolved_seed = int(seed if seed is not None else raw.get("seed", 42))
    resolved_id = job_id or raw.get("id") or f"{resolved_theme}-{resolved_seed}"

    return JobSpec(
        id=str(resolved_id),
        seed=resolved_seed,
        text=resolved_text,
        image=image,
        likeness_required=likeness,
        params=JobParams(
            category=category,
            theme=resolved_theme,
            size=resolved_size,
            palette_source=str(params_raw.get("palette_source") or "theme_asset"),
            symmetry=bool(params_raw.get("symmetry", False)),
            backend=resolved_backend if not image else str(params_raw.get("backend") or "procedural"),
            palette=palette,
        ),
        export=JobExport(formats=fmt_list),
        raw=raw,
    )
