"""Job Spec dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FORBIDDEN_THEMES = frozenset(
    {
        "cottage",
        "house",
        "tavern",
        "building",
        "wall",
        "roof",
        "architecture",
        "cabin",
        "barn",
    }
)

ALLOWED_CATEGORIES = frozenset({"prop", "item", "plant", "animal"})
ALLOWED_BACKENDS = frozenset({"procedural", "image_p1", "image_p2", "auto"})
ALLOWED_FORMATS = frozenset({"vox", "qb", "glb", "gltf"})


@dataclass
class JobParams:
    category: str = "prop"
    theme: str = "crate"
    size: tuple[int, int, int] = (16, 16, 16)
    palette_source: str = "theme_asset"
    symmetry: bool = False
    backend: str = "procedural"
    palette: list[tuple[int, int, int]] | None = None


@dataclass
class JobExport:
    formats: list[str] = field(default_factory=lambda: ["vox", "qb", "glb"])


@dataclass
class JobSpec:
    id: str
    seed: int = 42
    text: str | None = None
    image: str | None = None
    likeness_required: bool = False
    params: JobParams = field(default_factory=JobParams)
    export: JobExport = field(default_factory=JobExport)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "seed": self.seed,
            "text": self.text,
            "image": self.image,
            "likeness_required": self.likeness_required,
            "params": {
                "category": self.params.category,
                "theme": self.params.theme,
                "size": list(self.params.size),
                "palette_source": self.params.palette_source,
                "symmetry": self.params.symmetry,
                "backend": self.params.backend,
                "palette": [list(c) for c in self.params.palette] if self.params.palette else None,
            },
            "export": {"formats": list(self.export.formats)},
        }
