# kivyfn/three/parsers/glb/parser/context.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kivyfn.three.graphics.gl.texture import Texture2D
from kivyfn.three.parsers.glb.blueprint import GlbBlueprint


@dataclass(slots=True)
class GlbOptions:
    flip_v: bool = False
    flip_winding: bool = False


@dataclass(slots=True)
class GlbContext:
    gltf: Any
    filename: Path
    base_path: Path
    buffer_bytes: bytes
    blueprint: GlbBlueprint
    options: GlbOptions

    texture_cache: dict[int, Texture2D] = field(default_factory=dict)
    image_bytes_cache: dict[int, bytes] = field(default_factory=dict)
    image_texture_cache: dict[
        tuple[str, int | None, int | None, int | None, int | None],
        Texture2D,
    ] = field(default_factory=dict)


__all__ = (
    "GlbOptions",
    "GlbContext",
)
