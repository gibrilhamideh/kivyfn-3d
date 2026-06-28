# kivyfn/three/parsers/glb/asset.py
from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, cast

from kivyfn.three.math.transform import Transform
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.parsers.glb.instance import GlbInstance
from kivyfn.three.animations.library import AnimationLibrary
from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.types import AnimationTarget


BlueprintFilter = Callable[["GlbAsset"], bool]

@dataclass(slots=True)
class GlbPrimitive:
    name: str
    geometry: Geometry
    material: Material
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GlbAsset:
    name: str
    gltf_index: int

    primitives: list[GlbPrimitive] = field(default_factory=list)

    extras: dict[str, Any] = field(default_factory=dict)
    transform: Transform = field(default_factory=Transform)
    children: list[GlbAsset] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    _counter: int = 0

    @property
    def uid(self) -> str | None:
        return self.extras.get("uid")

    @property
    def is_renderable(self) -> bool:
        return bool(self.primitives)

    def _instantiate(
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
                child._instantiate(
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
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for blueprint in self.walk(
            include=include,
            exclude=exclude,
        ):
            if blueprint.is_renderable:
                blueprint.tags.add(tag)

    def untag(
        self,
        tag: str,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for blueprint in self.walk(
            include=include,
            exclude=exclude,
        ):
            if blueprint.is_renderable:
                blueprint.tags.discard(tag)

    def clear_tags(
        self,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for blueprint in self.walk(
            include=include,
            exclude=exclude,
        ):
            if blueprint.is_renderable:
                blueprint.tags.clear()

    # =================================== #
    # Traversal
    # =================================== #

    def walk(
        self,
        *,
        include_self: bool = True,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> Iterator[GlbAsset]:
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
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> list[GlbAsset]:
        return [
            blueprint
            for blueprint in self.walk(
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
            if blueprint.is_renderable
        ]

    def find(
        self,
        name: str,
        *,
        include_self: bool = True,
    ) -> GlbAsset | None:
        for blueprint in self.walk(
            include_self=include_self,
        ):
            if blueprint.name == name:
                return blueprint

        return None

    def require(
        self,
        name: str,
        *,
        include_self: bool = True,
    ) -> GlbAsset:
        blueprint = self.find(
            name,
            include_self=include_self,
        )

        if blueprint is None:
            raise ValueError(f"GlbAsset not found: {name!r}")

        return blueprint

    def _matches_walk(
        self,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> bool:
        if include is not None and not include(self):
            return False

        if exclude is not None and exclude(self):
            return False

        return True






@dataclass(slots=True)
class GlbBlueprint:
    assets: dict[str, GlbAsset] = field(default_factory=dict)
    tree: list[GlbAsset] = field(default_factory=list)
    animations: AnimationLibrary | None = None

    def instantiate(
        self,
        name: str | None = None,
        *,
        instance_name: str = "",
        new_material: bool = True,
    ) -> GlbInstance:

        animations = None
        by_gltf_index: dict[int, Node3D] = {}

        if name is None:
            root = self._instantiate_scene(
                by_gltf_index=by_gltf_index,
                name=instance_name,
                new_material=new_material,
            )
        else:
            asset = self.require(name)

            root = asset._instantiate(
                by_gltf_index=by_gltf_index,
                name=instance_name,
                new_material=new_material,
            )


        if self.animations is not None and not self.animations.is_empty:
            animations = self.animations.bind(
                AnimationBinding(
                    root=root,
                    targets=cast(
                        dict[AnimationTarget, Node3D],
                        by_gltf_index,
                    ),
                )
            )

        return GlbInstance(
            root=root,
            by_gltf_index=by_gltf_index,
            animations=animations
        )

    def _instantiate_scene(
        self,
        *,
        by_gltf_index: dict[int, Node3D],
        name: str = "",
        new_material: bool = True,
    ) -> Node3D:
        root = Node3D(
            name=name or "Scene",
        )

        for asset in self.tree:
            root.add_child(
                asset._instantiate(
                    by_gltf_index=by_gltf_index,
                    new_material=new_material,
                )
            )

        return root

    def find(
        self,
        name: str,
    ) -> GlbAsset | None:
        return self.assets.get(name)

    def require(
        self,
        name: str,
    ) -> GlbAsset:
        asset = self.find(name)

        if asset is None:
            raise ValueError(f"GlbAsset not found: {name!r}")

        return asset

    def walk(self):
        for root in self.tree:
            yield from root.walk()

    def renderables(self):
        for blueprint in self.walk():
            if blueprint.is_renderable:
                yield blueprint

    def tag(
        self,
        tag: str,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for asset in self.tree:
            asset.tag(
                tag,
                include=include,
                exclude=exclude,
            )

    def untag(
        self,
        tag: str,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for asset in self.tree:
            asset.untag(
                tag,
                include=include,
                exclude=exclude,
            )

    def clear_tags(
        self,
        *,
        include: BlueprintFilter | None = None,
        exclude: BlueprintFilter | None = None,
    ) -> None:
        for asset in self.tree:
            asset.clear_tags(
                include=include,
                exclude=exclude,
            )

    def __repr__(self) -> str:
        return (
            "GlbBlueprint(\n"
            f"  assets={len(self.assets)},\n"
            f"  roots={[obj.name for obj in self.tree]}\n"
            ")"
        )


