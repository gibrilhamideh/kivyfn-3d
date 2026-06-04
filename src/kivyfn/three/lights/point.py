# kivyfn/three/lights/point.py

from __future__ import annotations

from kivyfn.three.lights.base import Light3D


class PointLight(Light3D):
    def __init__(
        self,
        *,
        radius: float = 10.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.radius = radius
