# kivyfn/three/parsers/glb/node.py

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from kivyfn.three.math.transform import Transform
from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.parsers.glb.primitive import GlbPrimitive


GlbNodeFilter = Callable[["GlbNode"], bool]



@dataclass(slots=True)
class GlbNode:
    name: str
    gltf_index: int

    primitives: list[GlbPrimitive] = field(default_factory=list)
    morph_weights: tuple[float, ...] = ()

    transform: Transform = field(default_factory=Transform)
    children: list[GlbNode] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    skin_index: int | None = None

    _counter: int = 0

    @property
    def uid(self) -> str | None:
        value = self.extras.get("uid")

        if value is None:
            return None

        return str(value)

    @property
    def is_renderable(self) -> bool:
        return bool(self.primitives)

    def instantiate(
        self,
        *,
        by_gltf_index: dict[int, Node3D],
        name: str = "",
        new_material: bool = True,
    ) -> Node3D:
        node_name = name or self.generate_name()

        if len(self.primitives) == 1:
            node = self._instantiate_primitive(
                name=node_name,
                new_material=new_material,
            )

        else:
            node = self._instantiate_node(
                name=node_name,
                new_material=new_material,
            )

        by_gltf_index[self.gltf_index] = node

        for child in self.children:
            node.add_child(
                child.instantiate(
                    by_gltf_index=by_gltf_index,
                    new_material=new_material,
                )
            )

        return node

    def _instantiate_primitive(
        self,
        *,
        name: str,
        new_material: bool,
    ) -> Object3D:
        primitive = self.primitives[0]

        node = Object3D(
            name=name,
            uid=self.uid,
            geometry=primitive.geometry,
            material=(
                primitive.material.copy()
                if new_material
                else primitive.material
            ),
            tags=self.tags.copy(),
        )

        node.asset_name = self.name
        node.transform = self.transform.copy()

        return node

    def _instantiate_node(
        self,
        *,
        name: str,
        new_material: bool,
    ) -> Node3D:
        node = Node3D(
            name=name,
            uid=self.uid,
        )

        node.asset_name = self.name
        node.transform = self.transform.copy()

        for index, primitive in enumerate(self.primitives):
            child = Object3D(
                name=f"{name}.{index:03d}",
                geometry=primitive.geometry,
                material=(
                    primitive.material.copy()
                    if new_material
                    else primitive.material
                ),
                tags=self.tags.copy(),
            )

            child.asset_name = primitive.name
            node.add_child(child)

        return node

    def generate_name(self) -> str:
        self._counter += 1
        return f"{self.name}.{self._counter:03d}"

    # =================================== #
    # Tags
    # =================================== #

    def tag(
        self,
        tag: str,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for node in self.walk(
            include=include,
            exclude=exclude,
        ):
            if node.is_renderable:
                node.tags.add(tag)

    def untag(
        self,
        tag: str,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for node in self.walk(
            include=include,
            exclude=exclude,
        ):
            if node.is_renderable:
                node.tags.discard(tag)

    def clear_tags(
        self,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for node in self.walk(
            include=include,
            exclude=exclude,
        ):
            if node.is_renderable:
                node.tags.clear()

    # =================================== #
    # Traversal
    # =================================== #

    def walk(
        self,
        *,
        include_self: bool = True,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> Iterator[GlbNode]:
        if include_self and self._matches_walk(
            include=include,
            exclude=exclude,
        ):
            yield self

        for child in self.children:
            yield from child.walk(
                include_self=True,
                include=include,
                exclude=exclude,
            )

    def renderables(
        self,
        *,
        include_self: bool = True,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> list[GlbNode]:
        return [
            node
            for node in self.walk(
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
            if node.is_renderable
        ]

    def find(
        self,
        name: str,
        *,
        include_self: bool = True,
    ) -> GlbNode | None:
        for node in self.walk(
            include_self=include_self,
        ):
            if node.name == name:
                return node

        return None

    def require(
        self,
        name: str,
        *,
        include_self: bool = True,
    ) -> GlbNode:
        node = self.find(
            name,
            include_self=include_self,
        )

        if node is None:
            raise ValueError(f"GlbNode not found: {name!r}")

        return node

    def _matches_walk(
        self,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> bool:
        if include is not None and not include(self):
            return False

        if exclude is not None and exclude(self):
            return False

        return True
