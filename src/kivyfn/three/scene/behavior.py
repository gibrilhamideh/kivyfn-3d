# kivyfn/three/scene/controller.py
from __future__ import annotations


from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from kivyfn.three.scene.types import SceneObject
from kivyfn.three.scene.timeline.manager import TimelineManager



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


