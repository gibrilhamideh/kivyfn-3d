# kivyfn/three/scene/node.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.controls.interaction import InteractionEvent

class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)

    parent: Node3D | None = ObjectProperty(None, allownone=True)
    children: list[Node3D] = ListProperty([])


    pickable: bool = BooleanProperty(False)

    transform = ObjectProperty(None, allownone=True)

    __events__ = (
        "on_press",
        "on_release",
        "on_drag",
    )

    def __init__(
        self,
        name: str = "",
        transform: Transform | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.name = name
        self.transform = transform or Transform()

    @property
    def local_matrix(self) -> Matrix4:
        return self.transform.to_matrix4()

    @property
    def world_matrix(self) -> Matrix4:
        if self.parent is None:
            return self.local_matrix

        return self.parent.world_matrix @ self.local_matrix

    def add_child(self, child: Node3D) -> None:
        if child in self.children:
            return

        if child.parent is not None:
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

    def remove_child(self, child: Node3D) -> None:
        if child not in self.children:
            return

        self.children.remove(child)
        child.parent = None

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)

    def traverse(self):
        yield self

        for child in self.children:
            yield from child.traverse()

    def render(self, renderer: Renderer):
        pass

    def on_press(self, event: InteractionEvent) -> None:
        pass

    def on_release(self, event: InteractionEvent) -> None:
        pass

    def on_drag(self, event: InteractionEvent) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"Node3D("
            f"name={self.name!r}, "
            f"children={len(self.children)})"
        )
