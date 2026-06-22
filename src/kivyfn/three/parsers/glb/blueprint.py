# kivyfn/three/loaders/glb/asset.py
from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from kivyfn.three.math.transform import Transform
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject


BlueprintFilter = Callable[["GlbAsset"], bool]


@dataclass(slots=True)
class GlbAsset:
    name: str

    geometry: Geometry | None = None
    material: Material | None = None

    extras: dict[str, Any] = field(default_factory=dict)
    transform: Transform = field(default_factory=Transform)
    children: list[GlbAsset] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    @property
    def uid(self) -> str | None:
        return self.extras.get("uid")

    @property
    def is_renderable(self) -> bool:
        return self.geometry is not None

    def require_geometry(self) -> Geometry:
        if self.geometry is None:
            raise TypeError(f"GlbBlueprint {self.name!r} is not renderable.")

        return self.geometry

    def require_material(
        self,
        copy: bool = False,
    ) -> Material:
        if self.material is None:
            raise TypeError(f"GlbBlueprint {self.name!r} is not renderable.")

        if copy:
            return self.material.copy()

        return self.material

    def instantiate(
        self,
        *,
        name: str = "",
        new_material: bool = True,
    ) -> SceneObject:
        if self.is_renderable:
            node = Object3D(
                name=name or self.name,
                uid=self.uid,
                geometry=self.require_geometry(),
                material=self.require_material(copy=new_material),
                tags=self.tags,
            )
        else:
            node = Node3D(
                name=name or self.name,
                uid=self.uid,
            )

        node.transform = self.transform.copy()

        for child in self.children:
            node.add_child(
                child.instantiate(
                    new_material=new_material,
                )
            )

        return node

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
            raise ValueError(f"GlbBlueprint not found: {name!r}")

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
    assets: dict[str, GlbAsset] = field(
        default_factory=dict,
    )

    tree: list[GlbAsset] = field(
        default_factory=list,
    )

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
            "SceneBlueprint(\n"
            f"  objects={len(self.assets)},\n"
            f"  roots={[obj.name for obj in self.tree]}\n"
            ")"
        )


