# kivyfn/three/loaders/asset.py

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

    children: list["AssetObject"] = field(
        default_factory=list,
    )


@dataclass(slots=True)
class SceneAsset:

    objects: dict[str, AssetObject] = field(
        default_factory=dict,
    )

    tree: list[AssetObject] = field(
        default_factory=list,
    )
