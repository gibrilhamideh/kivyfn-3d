# kivyfn/three/loaders/obj/asset.py

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from kivyfn.three.math.transform import Transform
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject


@dataclass(slots=True)
class ObjBlueprint:
    name: str
    geometry: Geometry

    material: Material = field(default_factory=Material)
    transform: Transform = field(default_factory=Transform)

    def instantiate(
        self,
        *,
        material_copy: bool = False,
    ) -> SceneObject:
        node = Object3D(
            name=self.name,
            geometry=self.geometry,
            material=(
                self.material.copy()
                if material_copy
                else self.material
            ),
        )

        node.transform = self.transform.copy()

        return node

    def __repr__(self) -> str:
        return (
            "ObjBlueprint(\n"
            f"  name={self.name!r},\n"
            f"  geometry={self.geometry.name!r},\n"
            f"  material={self.material.name!r},\n"
            f"  transform={self.transform},\n"
            ")"
        )


@dataclass(slots=True)
class ObjSceneBlueprint:
    objects: dict[str, ObjBlueprint] = field(default_factory=dict)

    def walk_objects(self) -> Iterator[ObjBlueprint]:
        yield from self.objects.values()

    def __repr__(self) -> str:
        return (
            "ObjSceneBlueprint(\n"
            f"  objects={len(self.objects)},\n"
            f"  names={list(self.objects)},\n"
            ")"
        )
