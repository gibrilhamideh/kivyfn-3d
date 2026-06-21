# kivyfn/three/loaders/glb/asset.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from kivyfn.three.math.transform import Transform
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material

from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject

@dataclass(slots=True)
class GlbBlueprint:
    name: str

    geometry: Geometry | None = None
    material: Material | None = None

    extras: dict[str, Any] = field(default_factory=dict)
    transform: Transform = field(default_factory=Transform)
    children: list[GlbBlueprint] = field(default_factory=list)

    @property
    def uid(self) -> str | None:
        return self.extras.get("uid")

    @property
    def is_renderable(self):
        return self.geometry is not None

    def require_geometry(self) -> Geometry:
        if self.geometry is None:
            raise TypeError(f"AssetObject {self.name!r} is not renderable.")
        return self.geometry

    def require_material(self, copy=False) -> Material:
        if self.material is None:
            raise TypeError(f"AssetObject {self.name!r} is not renderable.")

        if copy:
            return self.material.copy()

        return self.material

    def __repr__(self) -> str:
        geometry_name = (
            self.geometry.name
            if self.geometry is not None
            else None
        )

        material_name = (
            self.material.name
            if self.material is not None
            else None
        )

        return (
            "GlbBlueprint(\n"
            f"  name={self.name!r},\n"
            f"  geometry={geometry_name!r},\n"
            f"  material={material_name!r},\n"
            f"  children={len(self.children)},\n"
            f"  is_renderable={self.is_renderable},\n"
            ")"
        )

    # TODO: need top change agrument copy becasue it ambiguis
    def instantiate(
        self,
        *,
        name: str = "",
        copy: bool = False,
    ) -> SceneObject:


        if self.is_renderable:
            node = Object3D(
                name=name or self.name,
                uid=self.uid,
                geometry=self.require_geometry(),
                material=self.require_material(copy=copy),
            )
        else:
            node = Node3D(
                name=self.name,
                uid=self.uid,
            )

        node.transform = self.transform.copy()

        for child in self.children:
            node.add_child(
                child.instantiate(
                    copy=copy,
                )
            )

        return node

    def print_tree(
        self,
        indent: int = 0,
    ) -> None:
        print(
            "  " * indent
            + repr(self)
        )

        for child in self.children:
            child.print_tree(indent + 1)


@dataclass(slots=True)
class GlbSceneBlueprint:
    objects: dict[str, GlbBlueprint] = field(
        default_factory=dict,
    )

    tree: list[GlbBlueprint] = field(
        default_factory=list,
    )

    def walk_tree(self):
        for root in self.tree:
            yield from self._walk_node(root)

    def walk_renderable(self):
        for blueprint in self.walk_tree():
            if blueprint.is_renderable:
                yield blueprint

    def _walk_node(
        self,
        blueprint: GlbBlueprint,
    ):
        yield blueprint

        for child in blueprint.children:
            yield from self._walk_node(child)

    def print_tree(self) -> None:
        for asset in self.tree:
            asset.print_tree()

    def __repr__(self) -> str:
        return (
            "SceneBlueprint(\n"
            f"  objects={len(self.objects)},\n"
            f"  roots={[obj.name for obj in self.tree]}\n"
            ")"
        )


