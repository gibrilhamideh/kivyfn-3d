# kivyfn/three/scene/node.py
from __future__ import annotations

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.transform import Transform


class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)

    parent = ObjectProperty(None, allownone=True)
    children = ListProperty([])

    transform = ObjectProperty(None, allownone=True)

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

        return (
            self.parent.world_matrix
            @ self.local_matrix
        )

    def add_child(
        self,
        child: "Node3D",
    ) -> None:
        if child in self.children:
            return

        if child.parent is not None:
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

    def remove_child(
        self,
        child: "Node3D",
    ) -> None:
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

    def __repr__(self) -> str:
        return (
            f"Node3D("
            f"name={self.name!r}, "
            f"children={len(self.children)})"
        )
