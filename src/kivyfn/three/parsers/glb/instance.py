# kivyfn/three/parsers/glb/instance.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.graph.node import Node3D
from kivyfn.three.animations.controller import AnimationController


@dataclass(slots=True)
class GlbInstance:
    root: Node3D
    by_gltf_index: dict[int, Node3D]
    animations: AnimationController | None = None
