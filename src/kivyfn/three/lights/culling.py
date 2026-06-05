# kivyfn/three/lights/culling.py

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.render.context import RenderContext
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
    point: int = 16
    spot: int = 16


class LightCuller:

    def __init__(
        self,
        registry: LightRegistry,
        *,
        limits: LightCullLimits | None = None,
    ) -> None:
        self.registry = registry
        self.limits = limits or LightCullLimits()

    # =================================== #
    # Public API
    # =================================== #
    def select(
        self,
        *,
        stage: RenderContext,
        view: View | None = None,
    ) -> CulledLights:
        stage_tags = self._stage_tags(stage)

        directional: list[DirectionalLight] = []
        point_candidates: list[tuple[float, PointLight]] = []
        spot_candidates: list[tuple[float, SpotLight]] = []

        view_position = None if view is None else view.position

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
                distance_sq = self._distance_to_view_sq(
                    light=light,
                    view_position=view_position,
                )

                if not self._is_inside_radius(
                    light=light,
                    distance_sq=distance_sq,
                ):
                    continue

                point_candidates.append((distance_sq, light))  # type: ignore[arg-type]
                continue

            if kind == "spot":
                distance_sq = self._distance_to_view_sq(
                    light=light,
                    view_position=view_position,
                )

                if not self._is_inside_radius(
                    light=light,
                    distance_sq=distance_sq,
                ):
                    continue

                spot_candidates.append((distance_sq, light))  # type: ignore[arg-type]
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

    def _is_inside_radius(
        self,
        *,
        light: Light3D,
        distance_sq: float,
    ) -> bool:
        radius = self._radius(light)

        if radius is None:
            return True

        return distance_sq <= radius * radius

    # =================================== #
    # Helpers
    # =================================== #
    def _stage_tags(
        self,
        stage: RenderContext,
    ) -> set[str]:
        tags = getattr(stage, "tags", None)

        if tags is None:
            return set()

        return set(tags)

    def _kind(
        self,
        light: Light3D,
    ) -> str:
        return str(getattr(light, "light_type", ""))

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

    def _distance_to_view_sq(
        self,
        *,
        light: Light3D,
        view_position: Vector3 | None,
    ) -> float:
        if view_position is None:
            return 0.0

        return self._distance_sq(
            light.world_position,
            view_position,
        )

    def _distance_sq(
        self,
        a: Vector3,
        b: Vector3,
    ) -> float:
        dx = a.x - b.x
        dy = a.y - b.y
        dz = a.z - b.z

        return dx * dx + dy * dy + dz * dz
