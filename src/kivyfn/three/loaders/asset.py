# kivyfn/three/loaders/asset.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, TypeGuard

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


class RenderableAsset(Protocol):
    name: str
    geometry: Geometry
    transform: Transform
    material: Material | None
    children: list[AssetObject]


def is_renderable(asset: AssetObject) -> TypeGuard[RenderableAsset]:
    """Type guard to ensure the given asset has a valid geometry."""
    return asset.geometry is not None


@dataclass(slots=True)
class SceneAsset:
    objects: dict[str, AssetObject] = field(
        default_factory=dict,
    )

    tree: list[AssetObject] = field(
        default_factory=list,
    )
