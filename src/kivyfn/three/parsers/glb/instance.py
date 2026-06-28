# kivyfn/three/parsers/glb/instance.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from kivyfn.three.graph.node import Node3D

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kivyfn.three.animations.controller import AnimationController


@dataclass(slots=True)
class GlbInstance:
    root: Node3D
    by_gltf_index: dict[int, Node3D]
    animations: AnimationController | None = None

    # =================================== #
    # GLTF Lookup
    # =================================== #

    def get_gltf_index(
        self,
        index: int,
    ) -> Node3D | None:
        return self.by_gltf_index.get(index)

    def require_gltf_index(
        self,
        index: int,
    ) -> Node3D:
        node = self.get_gltf_index(index)

        if node is None:
            raise ValueError(
                f"GLTF node index not found in instance: {index}"
            )

        return node

    # =================================== #
    # Animations
    # =================================== #

    @property
    def has_animations(self) -> bool:
        return self.animations is not None

    def require_animations(self) -> AnimationController:
        if self.animations is None:
            raise RuntimeError(
                f"GLB instance {self.root.name!r} has no animations."
            )

        return self.animations

    # =================================== #
    # Root Forwarding
    # =================================== #

    def walk(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Iterator[Node3D]:
        return self.root.walk(
            *args,
            **kwargs,
        )

    def find(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Node3D | None:
        return self.root.find(
            *args,
            **kwargs,
        )

    def require(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Node3D:
        return self.root.require(
            *args,
            **kwargs,
        )
