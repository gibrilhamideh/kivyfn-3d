# kivyfn/three/loaders/obj/asset.py

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from kivyfn.three.math.transform import Transform
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material


@dataclass(slots=True)
class ObjBlueprint:
    name: str
    geometry: Geometry

    material: Material = field(
        default_factory=Material,
    )

    transform: Transform = field(
        default_factory=Transform,
    )

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
