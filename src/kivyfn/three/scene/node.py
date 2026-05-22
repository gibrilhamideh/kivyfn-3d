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
from kivyfn.three.math.vector import Vector3
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.controls.interaction import InteractionEvent


class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)
    pickable: bool = BooleanProperty(False)
    grabable: bool = BooleanProperty(False)

    children: list[Node3D] = ListProperty([])
    parent: Node3D | None = ObjectProperty(None, allownone=True)
    transform: Transform = ObjectProperty()


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

    def __repr__(self) -> str:
        return (
            f"Node3D("
            f"name={self.name!r}, "
            f"children={len(self.children)})"
        )

    # =================================== #
    # Matrices
    # =================================== #
    @property
    def local_matrix(self) -> Matrix4:
        return self.transform.to_matrix4()

    @property
    def world_matrix(self) -> Matrix4:
        if self.parent is None:
            return self.local_matrix

        return self.parent.world_matrix @ self.local_matrix

    # =================================== #
    # Transform State
    # =================================== #
    @property
    def translation(self):
        return self.transform.translation

    @property
    def rotation(self) -> Quaternion:
        return self.transform.rotation

    @property
    def scale(self):
        return self.transform.scale

    # =================================== #
    # Translation
    # =================================== #
    def set_translation(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        self.transform.translation = (x, y, z)
        self.mark_transform_dirty()

    def translate_by(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        tx, ty, tz = self.transform.translation

        self.set_translation(
            tx + x,
            ty + y,
            tz + z,
        )

    # =================================== #
    # Scale
    # =================================== #
    def set_scale(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        self.transform.scale = (x, y, z)
        self.mark_transform_dirty()

    def scale_by(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        sx, sy, sz = self.transform.scale

        self.set_scale(
            sx * x,
            sy * y,
            sz * z,
        )

    # =================================== #
    # Rotation
    # =================================== #
    def set_rotation(
        self,
        rotation: Quaternion,
    ) -> None:
        self.transform.rotation = rotation.normalize()
        self.mark_transform_dirty()

    def rotate_by(
        self,
        angle_degrees: float,
        axis: Vector3 | tuple[float, float, float] = (0.0, 1.0, 0.0),
    ) -> None:
        if not isinstance(axis, Vector3):
            axis = Vector3(*axis)

        delta = Quaternion.from_axis_angle(
            axis,
            angle_degrees,
        )

        self.set_rotation(
            (delta * self.rotation).normalize()
        )


    # =================================== #
    # Dirty Propagation
    # =================================== #
    def mark_transform_dirty(self) -> None:
        instructions = getattr(self, "instructions", None)

        if instructions is not None:
            instructions.sync_transform()

        for child in self.children:
            child.mark_transform_dirty()

    # =================================== #
    # Relationships
    # =================================== #
    def add_child(
        self,
        child: Node3D,
    ) -> None:
        if child.parent is self:
            return

        if child.parent is not None:
            child.parent.remove_child(child)

        self.children.append(child)
        child.parent = self
        child.mark_transform_dirty()

    def remove_child(
        self,
        child: Node3D,
    ) -> None:
        self.children.remove(child)
        child.parent = None
        child.mark_transform_dirty()

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
    def attach(
        self,
        ctx: RenderContext,
    ) -> bool:
        """Override in renderable subclasses."""
        return False

    def detach(self) -> bool:
        """Override in renderable subclasses."""
        return False

    # =================================== #
    # Interaction Events
    # =================================== #
    def on_press(
        self,
        event: InteractionEvent,
    ) -> None:
        pass

    def on_release(
        self,
        event: InteractionEvent,
    ) -> None:
        pass

    def on_drag(
        self,
        event: InteractionEvent,
    ) -> None:
        pass


