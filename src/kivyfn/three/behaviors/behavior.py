# kivyfn/three/behaviors/behavior.py
from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from kivyfn.three.timeline.manager import TimelineManager

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject


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

    def remove(self) -> None:
        self.timelines.stop_all()


