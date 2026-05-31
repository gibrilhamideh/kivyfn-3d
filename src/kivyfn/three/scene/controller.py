# kivyfn/three/scene/controller.py
from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from kivy.event import EventDispatcher

from kivyfn.three.scene.timeline.manager import TimelineManager

if TYPE_CHECKING:
    from kivyfn.three.objects.object3d import Object3D
    from kivyfn.three.scene.node import Node3D



SceneNode: TypeAlias = "Node3D | Object3D"


class Controller(EventDispatcher):
    def __init__(
        self,
        node: SceneNode,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.node = node
        self.timelines = TimelineManager()


