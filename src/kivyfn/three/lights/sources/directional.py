# kivyfn/three/lights/sources/directional.py

from __future__ import annotations
from typing import Literal

from kivyfn.three.lights.sources.base import Light3D

class DirectionalLight(Light3D):

    @property
    def light_type(self) -> Literal["directional"]:
        return "directional"
