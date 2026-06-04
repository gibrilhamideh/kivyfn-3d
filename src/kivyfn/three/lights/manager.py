# kivyfn/three/lights/manager.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from kivyfn.three.lights.registry import LightRegistry
from kivyfn.three.lights.selection import LightSelection
from kivyfn.three.lights.sources.ambient import AmbientLight
from kivyfn.three.lights.sources.base import Light3D
from kivyfn.three.lights.sources.directional import DirectionalLight
from kivyfn.three.lights.sources.point import PointLight
from kivyfn.three.lights.sources.spot import SpotLight

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.render.context import RenderContext, RenderPass
    from kivyfn.three.views.view import View

    RenderStage = RenderContext | RenderPass


class LightManager(EventDispatcher):

    __events__ = (
        "on_light_dirty",
    )

    def __init__(self) -> None:
        super().__init__()

        self.registry = LightRegistry()
        self._dirty: set[str] = set()

    def __len__(self) -> int:
        return len(self.registry)

    def add(
        self,
        light: Light3D,
        *,
        tags: set[str] | None = None,
        parent: Node3D | None = None,
    ) -> Light3D:
        if not light.name:
            raise ValueError("Light must have a name before registration.")

        if parent is not None:
            parent.add_child(light)

        self.registry.add(
            light,
            tags=tags,
        )

        light.bind(
            on_light_dirty=self._on_light_dirty,
            on_transform_dirty=self._on_light_dirty,
            on_visibility_dirty=self._on_light_dirty,
        )

        self.dispatch_dirty(light)

        return light

    def remove(
        self,
        name: str,
    ) -> Light3D:
        record = self.registry.remove(name)
        light = record.light

        light.unbind(
            on_light_dirty=self._on_light_dirty,
            on_transform_dirty=self._on_light_dirty,
            on_visibility_dirty=self._on_light_dirty,
        )

        self._dirty.discard(name)

        if light.parent is not None:
            light.parent.remove_child(light)

        return light

    def get(
        self,
        name: str,
    ) -> Light3D | None:
        record = self.registry.get(name)
        return record.light if record is not None else None

    def require(
        self,
        name: str,
    ) -> Light3D:
        return self.registry.require(name).light

    def values(self) -> list[Light3D]:
        return [
            record.light
            for record in self.registry.values()
        ]



    def select(
        self,
        stage: RenderStage,
        view: View,
    ) -> LightSelection:
        selection = LightSelection()

        stage_tags = getattr(stage, "tags", set())

        for record in self.registry.values():
            light = record.light

            if not light.enabled:
                continue

            if not light.visible_in_tree:
                continue

            if record.tags and not record.tags.intersection(stage_tags):
                continue

            if isinstance(light, AmbientLight):
                selection.ambient.append(light)
                continue

            if isinstance(light, DirectionalLight):
                selection.directional.append(light)
                continue

            if isinstance(light, PointLight):
                selection.point.append(light)
                continue

            if isinstance(light, SpotLight):
                selection.spot.append(light)
                continue

        return selection




    def _on_light_dirty(
        self,
        light: Light3D,
        *_,
    ) -> None:
        self.dispatch_dirty(light)

    def dispatch_dirty(self, light: Light3D):
        self.dispatch("on_light_dirty", light)


    def on_light_dirty(self, light: Light3D) -> None:
        pass
