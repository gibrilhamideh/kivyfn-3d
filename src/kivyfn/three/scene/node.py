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
    from kivyfn.three.scene import Scene
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.render.render_pass import RenderPass
    from kivyfn.three.controls.interaction import InteractionEvent

class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)
    parent: Node3D | None = ObjectProperty(None, allownone=True)
    children: list[Node3D] = ListProperty([])
    pickable: bool = BooleanProperty(False)
    scene: Scene | None = ObjectProperty(None, allownone=True)
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

        if self.scene is not None:
            child.attach_scene(self.scene)

    def remove_child(self, child):
        if child in self.children:
            if child.scene is not None:
                child.detach_scene()

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
    def render(self, renderer: Renderer, render_pass: RenderPass):
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

    # =================================== #
    # Events
    # =================================== #
    def attach_scene(self, scene):
        self.scene = scene
        self.on_attach_scene(scene)

        for child in self.children:
            child.attach_scene(scene)

    def detach_scene(self):
        scene = self.scene

        for child in list(self.children):
            child.detach_scene()

        if scene is not None:
            self.on_detach_scene(scene)

        self.scene = None

    def on_attach_scene(self, scene):
        pass

    def on_detach_scene(self, scene):
        pass

