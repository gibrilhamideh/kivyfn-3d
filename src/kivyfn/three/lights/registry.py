# kivyfn/three/lights/registry.py

from __future__ import annotations

from collections import defaultdict

from kivyfn.three.types import (
        LightName, 
        LightSource,
        RenderPassName,
)


class LightRegistry:

    def __init__(self) -> None:
        self._lights: dict[LightName, LightSource] = {}
        self._tags: dict[str, set[LightName]] = defaultdict(set)

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

    def shadow_pass_name(
        self,
        light_name: LightName,
    ) -> RenderPassName:
        return light_name

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
        light: LightSource,
    ) -> LightName:

        base_name = light.config.base_name
        name = self.generate_name(base_name)

        light.name = name

        self._lights[name] = light
        self._index_light(
            name=name,
            light=light,
        )

        return name

    def remove(
        self,
        name: LightName,
    ) -> LightSource:
        light = self.require(name)

        self._unindex_light(name)

        del self._lights[name]

        return light

    def reindex(
        self,
        light: LightSource,
    ) -> None:
        self._unindex_light(light.name)
        self._index_light(
            name=light.name,
            light=light,
        )

    def get(
        self,
        name: LightName,
    ) -> LightSource | None:
        return self._lights.get(name)

    def require(
        self,
        name: LightName,
    ) -> LightSource:
        light = self.get(name)

        if light is None:
            raise ValueError(
                f"Light {name!r} is not registered."
            )

        return light




    # =================================== #
    # Tag API
    # =================================== #
    def lights_of(
        self,
        tag: str,
    ) -> list[LightSource]:
        return [
            self._lights[name]
            for name in self._tags.get(tag, set())
            if name in self._lights
        ]


    def tags(self) -> set[str]:
        return set(self._tags.keys())

    # =================================== #
    # Internal
    # =================================== #
    def _index_light(
        self,
        *,
        name: LightName,
        light: LightSource,
    ) -> None:
        affected_tags = light.config.affected_tags

        if not affected_tags:
            self._tags[""].add(name)
            return

        for tag in affected_tags:
            self._tags[tag].add(name)

    def _unindex_light(
        self,
        name: LightName,
    ) -> None:
        empty_tags: list[str] = []

        for tag, names in self._tags.items():
            names.discard(name)

            if not names:
                empty_tags.append(tag)

        for tag in empty_tags:
            del self._tags[tag]
