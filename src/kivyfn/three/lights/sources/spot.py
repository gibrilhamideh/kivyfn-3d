# kivyfn/three/lights/spot.py


from __future__ import annotations

from kivy.properties import NumericProperty

from kivyfn.three.lights.sources.base import Light3D
from kivyfn.three.math.vector import Vector3


class SpotLight(Light3D):

    radius: float = NumericProperty(10.0)
    angle: float = NumericProperty(45.0)

    def __init__(
        self,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.bind(
            radius=self.mark_light_dirty,
            angle=self.mark_light_dirty,
        )

    @property
    def direction(self) -> Vector3:
        return self.world_forward

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(\n"
            f"    name={self.name!r},\n"
            f"    color={tuple(self.color)},\n"
            f"    intensity={self.intensity},\n"
            f"    radius={self.radius},\n"
            f"    angle={self.angle},\n"
            f"    enabled={self.enabled},\n"
            ")"
        )
