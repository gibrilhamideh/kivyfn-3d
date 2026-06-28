# kivyfn/three/parsers/glb/node.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material



@dataclass(slots=True)
class GlbPrimitive:
    name: str
    geometry: Geometry
    material: Material
    extras: dict[str, Any] = field(default_factory=dict)
