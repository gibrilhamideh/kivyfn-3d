# kivyfn/three/loaders/asset.py

from __future__ import annotations
from dataclasses import dataclass, field

from kivyfn.three.math.transform import Transform
from kivyfn.three.objects.geometry import Geometry
from kivyfn.three.objects.material import Material


@dataclass(slots=True)
class AssetObject:
    name: str

    geometry: Geometry | None = None

    transform: Transform = field(
        default_factory=Transform,
    )

    material: Material | None = None

    children: list[AssetObject] = field(
        default_factory=list,
    )

    @property
    def is_renderable(self):
        return self.geometry is not None

    def require_geometry(self) -> Geometry:
        if self.geometry is None:
            raise TypeError(f"AssetObject {self.name!r} is not renderable.")
        return self.geometry

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
            "AssetObject(\n"
            f"  name={self.name!r},\n"
            f"  geometry={geometry_name!r},\n"
            f"  material={material_name!r},\n"
            f"  children={len(self.children)},\n"
            f"  is_renderable={self.is_renderable},\n"
            ")"
        )

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
class SceneAsset:
    objects: dict[str, AssetObject] = field(
        default_factory=dict,
    )

    tree: list[AssetObject] = field(
        default_factory=list,
    )

    def walk_tree(self):
        for root in self.tree:
            yield from self._walk_node(root)

    def walk_renderable(self):
        for asset in self.walk_tree():
            if asset.is_renderable:
                yield asset

    def _walk_node(
        self,
        asset: AssetObject,
    ):
        yield asset

        for child in asset.children:
            yield from self._walk_node(child)

    def print_tree(self) -> None:
        for asset in self.tree:
            asset.print_tree()

    def __repr__(self) -> str:
        return (
            "SceneAsset(\n"
            f"  objects={len(self.objects)},\n"
            f"  roots={[obj.name for obj in self.tree]}\n"
            ")"
        )


