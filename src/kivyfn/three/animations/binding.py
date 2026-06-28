# kivyfn/three/animations/binding.py

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from kivyfn.three.animations.types import AnimationTarget
from kivyfn.three.graph.node import Node3D


@dataclass(slots=True)
class AnimationBinding:
    root: Node3D
    targets: Mapping[AnimationTarget, Node3D]

    def get(
        self,
        target: AnimationTarget,
    ) -> Node3D | None:
        return self.targets.get(target)

    def require(
        self,
        target: AnimationTarget,
    ) -> Node3D:
        node = self.get(target)

        if node is None:
            raise ValueError(
                f"Animation target not found: {target!r}"
            )

        return node
