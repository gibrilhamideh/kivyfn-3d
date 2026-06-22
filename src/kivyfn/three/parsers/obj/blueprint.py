# kivyfn/three/loaders/obj/asset.py

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject


@dataclass(slots=True)
class ObjAsset:
    name: str
    geometry: Geometry

    material: Material = field(default_factory=Material)
    transform: Transform = field(default_factory=Transform)
    tags: set[str] = field(default_factory=set)

    def instantiate(
        self,
        *,
        name: str = "",
        new_matrial: bool = False,
    ) -> SceneObject:
        node = Object3D(
            name=name or self.name,
            geometry=self.geometry,
            material=(
                self.material.copy()
                if new_matrial
                else self.material
            ),
            tags=self.tags,
        )

        node.transform = self.transform.copy()
        return node

    def tag(self, tag: str) -> None:
        self.tags.add(tag)

    def untag(self, tag: str) -> None:
        self.tags.discard(tag)

    def clear_tags(self) -> set[str]:
        old_tags = set(self.tags)
        self.tags.clear()
        return old_tags

    def __repr__(self) -> str:
        return (
            "ObjAsset(\n"
            f"  name={self.name!r},\n"
            f"  geometry={self.geometry.name!r},\n"
            f"  material={self.material.name!r},\n"
            f"  transform={self.transform},\n"
            f"  tags={sorted(self.tags)!r},\n"
            ")"
        )


@dataclass(slots=True)
class ObjBlueprint:
    assets: dict[str, ObjAsset] = field(default_factory=dict)

    def walk(self) -> Iterator[ObjAsset]:
        yield from self.assets.values()

    def tag(self, tag: str) -> None:
        for asset in self.walk():
            asset.tag(tag)

    def untag(self, tag: str) -> None:
        for asset in self.walk():
            asset.untag(tag)

    def clear_tags(self) -> None:
        for asset in self.walk():
            asset.clear_tags()

    def __repr__(self) -> str:
        return (
            "ObjBlueprint(\n"
            f"  assets={len(self.assets)},\n"
            f"  names={list(self.assets)},\n"
            ")"
        )
