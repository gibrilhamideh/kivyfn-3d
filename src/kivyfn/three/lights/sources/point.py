# kivyfn/three/lights/sources/point.py

from __future__ import annotations
from typing import Literal

from kivy.properties import NumericProperty
from kivyfn.three.lights.sources.base import Light3D



class PointLight(Light3D):

    radius: float = NumericProperty(10.0)

    def __init__(
        self,
        radius: float = 10.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.radius = radius
        self.bind(radius=self.mark_light_dirty)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(\n"
            f"    name={self.name!r},\n"
            f"    color={tuple(self.color)},\n"
            f"    intensity={self.intensity},\n"
            f"    radius={self.radius},\n"
            f"    enabled={self.enabled},\n"
            ")"
        )

    @property
    def light_type(self) -> Literal["point"]:
        return "point"
