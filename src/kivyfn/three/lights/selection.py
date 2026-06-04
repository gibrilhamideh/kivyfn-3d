# kivyfn/three/lights/selection.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.lights.sources.ambient import AmbientLight
from kivyfn.three.lights.sources.directional import DirectionalLight
from kivyfn.three.lights.sources.point import PointLight
from kivyfn.three.lights.sources.spot import SpotLight


@dataclass(slots=True)
class LightSelection:
    ambient: list[AmbientLight] = field(default_factory=list)
    directional: list[DirectionalLight] = field(default_factory=list)
    point: list[PointLight] = field(default_factory=list)
    spot: list[SpotLight] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(
            self.ambient
            or self.directional
            or self.point
            or self.spot
        )
