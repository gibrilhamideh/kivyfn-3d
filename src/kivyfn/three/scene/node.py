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
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.controls.interaction import InteractionEvent

class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)
    parent: Node3D | None = ObjectProperty(None, allownone=True)
    children: list[Node3D] = ListProperty([])
    pickable: bool = BooleanProperty(False)
    transform: Transform = ObjectProperty()

    __events__ = (
        "on_press",
        "on_release",
        "on_drag",
    )


    def __repr__(self) -> str:
        return (
            f"Node3D("
            f"name={self.name!r}, "
            f"children={len(self.children)})"
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

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)

    def traverse(self):
        yield self

        for child in self.children:
            yield from child.traverse()

    # =================================== #
    # Render
    # =================================== #
    def build(self, renderer: Renderer):
        pass

    # =================================== #
    # Interaction Evenets
    # =================================== #
    def on_press(self, event: InteractionEvent) -> None:
        pass

    def on_release(self, event: InteractionEvent) -> None:
        pass

    def on_drag(self, event: InteractionEvent) -> None:
        pass


