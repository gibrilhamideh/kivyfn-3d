# kivyfn/three/behaviors/behavior.py
from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias

from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from kivyfn.three.timeline.manager import TimelineManager

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.assets.object3d import Object3D

SceneObject: TypeAlias = "Node3D | Object3D"

class Behavior(EventDispatcher):
    name: str = StringProperty("")

    def __init__(
        self,
        node: SceneObject,
        name: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.node = node
        self.name = name or self.__class__.__name__
        self.timelines = TimelineManager()

    def destroy(self) -> None:
        self.timelines.stop_all()


