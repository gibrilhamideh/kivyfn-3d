# kivyfn/three/lights/spot.py

from __future__ import annotations

from kivyfn.three.lights.base import Light3D


class SpotLight(Light3D):
    def __init__(
        self,
        *,
        radius: float = 10.0,
        angle: float = 45.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.radius = radius
        self.angle = angle
