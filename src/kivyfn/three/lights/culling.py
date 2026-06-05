# kivyfn/three/lights/culling.py

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.views.view import View

    from kivyfn.three.lights.registry import LightRegistry
    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight


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
class LightCullLimits:
    directional: int = 4
    point: int = 4
    spot: int = 5


@dataclass(slots=True, frozen=True)
class LightCullConfig:
    view_lerp: float = 0.75

    # Wider than camera FOV on purpose.
    # This is not exact frustum culling yet; it is a stable rough view cone.
    view_margin_degrees: float = 35.0

    # Keep lights behind the camera only if they are close to the culling point.
    allow_behind_camera: bool = False


class LightCuller:

    def __init__(
        self,
        registry: LightRegistry,
        *,
        limits: LightCullLimits | None = None,
        config: LightCullConfig | None = None,
    ) -> None:
        self.registry = registry
        self.limits = limits or LightCullLimits()
        self.config = config or LightCullConfig()

    # =================================== #
    # Public API
    # =================================== #

    def select(
        self,
        *,
        stage_tags: set[str],
        view: View | None = None,
    ) -> CulledLights:

        directional: list[DirectionalLight] = []
        point_candidates: list[tuple[float, PointLight]] = []
        spot_candidates: list[tuple[float, SpotLight]] = []

        culling_point = self._view_culling_point(view)

        for light in self.registry.values():

            if not self._is_active(light):
                continue

            if not self._affects_stage(light, stage_tags):
                continue

            kind = self._kind(light)

            if kind == "directional":
                directional.append(light)  # type: ignore[arg-type]
                continue

            if kind == "point":
                if not self._is_roughly_in_view(light, view):
                    continue

                score = self._distance_to_point_sq(
                    light=light,
                    point=culling_point,
                )

                point_candidates.append((score, light))  # type: ignore[arg-type]
                continue

            if kind == "spot":
                if not self._is_roughly_in_view(light, view):
                    continue

                score = self._distance_to_point_sq(
                    light=light,
                    point=culling_point,
                )

                spot_candidates.append((score, light))  # type: ignore[arg-type]
                continue

        point_candidates.sort(key=lambda item: item[0])
        spot_candidates.sort(key=lambda item: item[0])

        return CulledLights(
            directional=directional[:self.limits.directional],
            point=[
                light
                for _, light in point_candidates[:self.limits.point]
            ],
            spot=[
                light
                for _, light in spot_candidates[:self.limits.spot]
            ],
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

    def _affects_stage(
        self,
        light: Light3D,
        stage_tags: set[str],
    ) -> bool:
        affected_tags = set(light.config.affected_tags)

        if not affected_tags:
            return True

        return bool(affected_tags & stage_tags)

    def _is_roughly_in_view(
        self,
        light: Light3D,
        view: View | None,
    ) -> bool:
        if view is None:
            return True

        radius = self._radius(light)
        light_position = light.world_position

        view_to_light = light_position - view.position
        distance = view_to_light.length

        if distance <= 0.000001:
            return True

        direction_to_light = view_to_light / distance
        view_forward = (view.target - view.position).normalize()

        dot = view_forward.dot(direction_to_light)

        if dot >= 0.0:
            return self._inside_view_cone(
                dot=dot,
                view=view,
                radius=radius,
                distance=distance,
            )

        if self.config.allow_behind_camera:
            return True

        return False

    def _inside_view_cone(
        self,
        *,
        dot: float,
        view: View,
        radius: float | None,
        distance: float,
    ) -> bool:
        fov = float(getattr(view, "fov", 45.0))

        half_angle = math.radians(
            (fov * 0.5) + self.config.view_margin_degrees
        )

        if radius is not None and distance > 0.000001:
            radius_angle = math.atan(radius / distance)
            half_angle += radius_angle

        min_dot = math.cos(
            min(half_angle, math.pi)
        )

        return dot >= min_dot

    # =================================== #
    # Scoring
    # =================================== #

    def _view_culling_point(
        self,
        view: View | None,
    ) -> Vector3 | None:
        if view is None:
            return None

        return view.position.lerp(
            view.target,
            self.config.view_lerp,
        )

    def _distance_to_point_sq(
        self,
        *,
        light: Light3D,
        point: Vector3 | None,
    ) -> float:
        if point is None:
            return 0.0

        return self._distance_sq(
            light.world_position,
            point,
        )

    # =================================== #
    # Helpers
    # =================================== #

    def _kind(
        self,
        light: Light3D,
    ) -> str:
        return light.light_type

    def _radius(
        self,
        light: Light3D,
    ) -> float | None:
        radius = getattr(light, "radius", None)

        if radius is None:
            radius = getattr(light, "distance", None)

        if radius is None:
            radius = getattr(light, "range", None)

        if radius is None:
            return None

        radius = float(radius)

        if not math.isfinite(radius) or radius <= 0.0:
            return None

        return radius

    def _distance_sq(
        self,
        a: Vector3,
        b: Vector3,
    ) -> float:
        dx = a.x - b.x
        dy = a.y - b.y
        dz = a.z - b.z

        return dx * dx + dy * dy + dz * dz
