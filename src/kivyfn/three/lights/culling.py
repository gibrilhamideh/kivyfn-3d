# kivyfn/three/lights/culling.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeGuard

import math

from dataclasses import dataclass, field
from heapq import nsmallest

from kivyfn.three.types import LightSource

if TYPE_CHECKING:
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.views.view import View

    from kivyfn.three.lights.limits import LightLimits
    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight


EPSILON = 1e-8


@dataclass(slots=True)
class CulledLights:
    directional: list[DirectionalLight] = field(default_factory=list)
    point: list[PointLight] = field(default_factory=list)
    spot: list[SpotLight] = field(default_factory=list)

    def __len__(self) -> int:
        return (
            len(self.directional)
            + len(self.point)
            + len(self.spot)
        )


@dataclass(slots=True, frozen=True)
class LightCullConfig:
    view_lerp: float = 0.75
    view_margin_degrees: float = 35.0
    allow_behind_camera: bool = False


class LightCuller:

    def __init__(
        self,
        *,
        limits: LightLimits,
        config: LightCullConfig | None = None,
    ) -> None:
        self.limits = limits
        self.config = config or LightCullConfig()

    # =================================== #
    # Public API
    # =================================== #

    def select(
        self,
        *,
        lights: list[LightSource],
        view: View,
    ) -> CulledLights:

        directional: list[DirectionalLight] = []
        point_candidates: list[PointLight] = []
        spot_candidates: list[SpotLight] = []

        culling_point = self._view_culling_point(view)
        forward = (view.target - view.position).normalize()
        view_cone_angle = math.radians(
            (view.fov * 0.5)
            + self.config.view_margin_degrees
        )

        for light in lights:

            if not self._is_active(light):
                continue

            if self._is_directional(light):
                directional.append(light)
                continue

            if self._is_point(light):
                if not self._is_in_view(light, view, forward, view_cone_angle):
                    continue

                point_candidates.append(light)
                continue

            if self._is_spot(light):
                if not self._is_in_view(light, view, forward, view_cone_angle):
                    continue

                spot_candidates.append(light)
                continue

        point_candidates = nsmallest(
            self.limits.point,
            point_candidates,
            key=lambda light: self._distance_to_point_sq(
                light=light,
                point=culling_point,
            ),
        )

        spot_candidates = nsmallest(
            self.limits.spot,
            spot_candidates,
            key=lambda light: self._distance_to_point_sq(
                light=light,
                point=culling_point,
            ),
        )

        return CulledLights(
            directional=directional,
            point=point_candidates,
            spot=spot_candidates,
        )

    # =================================== #
    # Filters
    # =================================== #

    def _is_active(
        self,
        light: Light3D,
    ) -> bool:
        return bool(
            light.enabled
            and light.visible_in_tree
        )

    def _is_in_view(
        self,
        light: SpotLight | PointLight,
        view: View,
        forward: Vector3,
        view_cone_angle: float
    ) -> bool:
        light_position = light.world_position

        view_to_light = light_position - view.position
        distance = view_to_light.length

        if distance <= EPSILON:
            return True

        direction_to_light = view_to_light / distance

        dot = forward.dot(direction_to_light)

        if dot >= 0.0:
            return self._inside_view_cone(
                dot=dot,
                radius=light.radius,
                distance=distance,
                view_cone_angle=view_cone_angle
            )

        if self.config.allow_behind_camera:
            return True

        return False

    def _inside_view_cone(
        self,
        *,
        dot: float,
        radius: float,
        distance: float,
        view_cone_angle: float,
    ) -> bool:

        if distance > EPSILON:
            radius_angle = math.atan(radius / distance)
            view_cone_angle += radius_angle

        min_dot = math.cos(min(view_cone_angle, math.pi))
        return dot >= min_dot

    # =================================== #
    # Scoring
    # =================================== #

    def _view_culling_point(
        self,
        view: View,
    ) -> Vector3:

        return view.position.lerp(
            view.target,
            self.config.view_lerp,
        )

    def _distance_to_point_sq(
        self,
        *,
        light: LightSource,
        point: Vector3,
    ) -> float:
        return light.world_position.distance_sq(point)


    def _is_directional(
        self,
        light: LightSource,
    ) -> TypeGuard[DirectionalLight]:
        return light.light_type == "directional"


    def _is_point(
        self,
        light: LightSource,
    ) -> TypeGuard[PointLight]:
        return light.light_type == "point"


    def _is_spot(
        self,
        light: LightSource,
    ) -> TypeGuard[SpotLight]:
        return light.light_type == "spot"


