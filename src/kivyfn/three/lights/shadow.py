# kivyfn/three/lights/shadow.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from kivyfn.three.math.vector import Vector3


ShadowType = Literal[
    "directional",
    "spot",
    "point",
]


@dataclass(slots=True)
class LightShadow:
    shadow_type: ShadowType

    resolution: int = 2048

    caster_tags: set[str] | None = None
    receiver_tags: set[str] | None = None

    view_names: tuple[str, ...] = field(default_factory=tuple)
    pass_names: tuple[str, ...] = field(default_factory=tuple)

    texture_uniform: str = "shadow_texture"
    view_uniform: str = "shadow_view_mat"
    projection_uniform: str = "shadow_projection_mat"

    target: Vector3 = field(
        default_factory=Vector3.zero,
    )

    distance: float = 512.0
    near: float = 0.1
    far: float = 1024.0
    ortho_size: float = 256.0

    bias: float = 0.005
    normal_bias: float = 0.05
