# kivyfn/three/animations/binding.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from kivyfn.three.graph.node import Node3D
from kivyfn.three.animations.types import (
    AnimationTarget,
    AnimationTargetProtocol,
)


@dataclass(slots=True)
class AnimationBinding:
    root: Node3D
    targets: Mapping[
        AnimationTarget,
        AnimationTargetProtocol,
    ]

    def get(
        self,
        target: AnimationTarget,
    ) -> AnimationTargetProtocol | None:
        return self.targets.get(
            target,
        )

    def require(
        self,
        target: AnimationTarget,
    ) -> AnimationTargetProtocol:
        animation_target = self.get(
            target,
        )

        if animation_target is None:
            raise ValueError(
                f"Animation target not found: {target!r}"
            )

        return animation_target
