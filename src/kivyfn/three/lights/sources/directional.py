# kivyfn/three/lights/sources/directional.py

from __future__ import annotations

from kivyfn.three.lights.sources.base import Light3D
from kivyfn.three.math.vector import Vector3


class DirectionalLight(Light3D):

    @property
    def direction(self) -> Vector3:
        return self.world_forward
