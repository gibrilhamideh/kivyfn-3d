# kiyvfn/three/render/geomerty.py
from __future__ import annotations
from typing import Literal
from dataclasses import dataclass, field
from kivy.graphics.texture import Texture


RenderMode = Literal[
    "points",
    "line_strip",
    "line_loop",
    "lines",
    "triangles",
    "triangle_strip",
    "triangle_fan"
]

@dataclass(slots=True)
class Geometry:
    name: str | None = None

    fmt: list[tuple[bytes, int, str]] = field(default_factory=lambda: [
        (b"v_pos", 3, "float"),
        (b"v_normal", 3, "float"),
        (b"v_tc0", 2, "float"),
    ])

    vertices: list[float] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)
    mode: RenderMode = "triangles"
    texture: Texture | None = None 

