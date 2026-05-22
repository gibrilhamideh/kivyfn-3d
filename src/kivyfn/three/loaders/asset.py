# kivyfn/three/loaders/asset.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.math.transform import Transform
from kivyfn.three.objects import Geometry, Material

@dataclass(slots=True)
class AssetObject:
    name: str
    geometry: Geometry
    transform: Transform = field(default_factory=Transform)
    material: Material | None = None


@dataclass(slots=True)
class SceneAsset:
    objects: dict[str, AssetObject] = field(default_factory=dict)
