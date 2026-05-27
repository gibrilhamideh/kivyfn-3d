# kivyfn/three/light/manager.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.base import Light3D



class LightManager(EventDispatcher):


    __events__ = ("on_dirty", )

    def __init__(
        self,
        root: Node3D,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.root = root
        self._lights: dict[str, Light3D] = {}

    def __len__(self) -> int:
        return len(self._lights)

    def add(
        self,
        light: Light3D,
        parent: Node3D | None = None,
    ) -> None:
        if light.name in self._lights:
            raise ValueError(f"Light already exists: {light.name!r}")

        light.bind(on_dirty=self.dispatch_dirty)

        parent = parent or self.root
        parent.add_child(light)

        self._lights[light.name] = light
        self.dispatch_dirty()


    def remove(
        self,
        name: str,
    ) -> Light3D | None:
        light = self._lights.pop(name, None)

        if light is None:
            return None

        if light.parent is not None:
            light.parent.remove_child(light)

        light.unbind(on_ditry=self.dispatch_dirty)
        self.dispatch_dirty()
        return light

    def get(
        self,
        name: str,
    ) -> Light3D:
        try:
            return self._lights[name]
        except KeyError:
            raise KeyError(f"Light does not exist: {name!r}") from None

    def exists(
        self,
        name: str,
    ) -> bool:
        return name in self._lights

    def names(self) -> list[str]:
        return list(self._lights.keys())

    def values(self) -> list[Light3D]:
        return list(self._lights.values())

    def clear(self) -> None:
        for name in list(self._lights.keys()):
            self.remove(name)

    # =================================== #
    # Disptach
    # =================================== #
    def dispatch_dirty(self, *_):
        self.dispatch("on_dirty")


    # =================================== #
    # Events
    # =================================== #
    def on_dirty(self):
        pass
