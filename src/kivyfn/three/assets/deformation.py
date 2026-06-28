# kivyfn/three/assets/deformation.py

# kivyfn/three/assets/deformation.py

from __future__ import annotations

from dataclasses import dataclass, field
from kivyfn.three.assets.skin import Skin


@dataclass(slots=True)
class Deformation:
    """
    Per-object vertex deformation state.

    Geometry owns static deformation data:
        - morph targets
        - v_joints / v_weights

    Deformation owns object-local runtime deformation state:
        - current morph target weights
        - optional skin binding
    """

    morph_weights: list[float] = field(default_factory=list)
    skin: Skin | None = None

    @property
    def has_morph_weights(self) -> bool:
        return bool(self.morph_weights)

    @property
    def has_skin(self) -> bool:
        return self.skin is not None

