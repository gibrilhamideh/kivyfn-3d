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


@dataclass(slots=True)
class SceneAsset:
    objects: dict[str, AssetObject] = field(
        default_factory=dict,
    )

    tree: list[AssetObject] = field(
        default_factory=list,
    )
