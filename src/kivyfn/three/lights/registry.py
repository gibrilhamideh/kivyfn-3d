# kivyfn/three/lights/registry.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivyfn.three.types import LightName, RenderPassName, ViewName

if TYPE_CHECKING:
    from kivyfn.three.lights.sources.base import Light3D


class LightRegistry:

    def __init__(self) -> None:
        self._lights: dict[LightName, Light3D] = {}
        self._ids: dict[int, LightName] = {}

    def __len__(self) -> int:
        return len(self._lights)

    # =================================== #
    # Name Generation
    # =================================== #
    def generate_name(
        self,
        base_name: str,
    ) -> LightName:
        index = 1

        while True:
            name = f"{base_name}.{index:03d}"

            if name not in self._lights:
                return name

            index += 1

    def shadow_view_name(
        self,
        light_name: LightName,
    ) -> ViewName:
        return light_name

    def shadow_pass_name(
        self,
        light_name: LightName,
    ) -> RenderPassName:
        return light_name

    def point_shadow_view_name(
        self,
        light_name: LightName,
        face: str,
    ) -> ViewName:
        return f"{light_name}.{face}"

    def point_shadow_pass_name(
        self,
        light_name: LightName,
        face: str,
    ) -> RenderPassName:
        return f"{light_name}.{face}"

    # =================================== #
    # Registry API
    # =================================== #
    def add(
        self,
        light: Light3D,
    ) -> LightName:
        light_id = id(light)

        if light_id in self._ids:
            return self._ids[light_id]

        base_name = light.config.base_name
        name = self.generate_name(base_name)

        light.name = name

        self._lights[name] = light
        self._ids[light_id] = name

        return name

    def remove(
        self,
        name: LightName,
    ) -> Light3D:
        light = self.require(name)

        del self._lights[name]
        del self._ids[id(light)]

        return light

    def get(
        self,
        name: LightName,
    ) -> Light3D | None:
        return self._lights.get(name)

    def get_by_id(
        self,
        light: Light3D,
    ) -> Light3D | None:
        name = self._ids.get(id(light))

        if name is None:
            return None

        return self._lights.get(name)

    def require(
        self,
        name: LightName,
    ) -> Light3D:
        light = self.get(name)

        if light is None:
            raise ValueError(
                f"Light {name!r} is not registered."
            )

        return light

    def name_of(
        self,
        light: Light3D,
    ) -> LightName | None:
        return self._ids.get(id(light))

    def require_name_of(
        self,
        light: Light3D,
    ) -> LightName:
        name = self.name_of(light)

        if name is None:
            raise ValueError(
                f"Light {light!r} is not registered."
            )

        return name

    def contains(
        self,
        name: LightName,
    ) -> bool:
        return name in self._lights

    def values(self) -> list[Light3D]:
        return list(self._lights.values())

    def names(self) -> list[LightName]:
        return list(self._lights.keys())

    def items(self) -> list[tuple[LightName, Light3D]]:
        return list(self._lights.items())

