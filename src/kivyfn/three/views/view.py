# kivyfn/three/scene/view.py

from __future__ import annotations
from typing import Literal
import math

from kivy.event import EventDispatcher
from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        OptionProperty,
)

from kivyfn.three.math.vector import Vector3
from kivyfn.three.math.matrix import Matrix4


class View(EventDispatcher):

    position: Vector3 = ObjectProperty(None, allownone=True)
    target: Vector3 = ObjectProperty(None, allownone=True)
    up: Vector3 = ObjectProperty(None, allownone=True)

    fov: float = NumericProperty(45.0)
    near: float = NumericProperty(1.0)
    far: float = NumericProperty(1000.0)

    ortho_size: float = NumericProperty(20.0)
    projection: Literal[
        "perspective",
        "orthographic"
        ] = OptionProperty("perspective", options=["perspective", "orthographic"])

    __events__ = ("on_view_dirty", )

    def __repr__(self) -> str:
        return (
            "View(\n"
            f"  projection_type={self.projection!r},\n"
            f"  fov={self.fov:.1f},\n"
            f"  position={self.position},\n"
            f"  target={self.target},\n"
            f"  up={self.up}\n"
            ")"
        )

    def __init__(
        self,
        position: Vector3 | None = None,
        target: Vector3 | None = None,
        up: Vector3 | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.position = position or Vector3(0.0, 0.0, 10.0)
        self.target = target or Vector3.zero()
        self.up = up or Vector3(0.0, 1.0, 0.0)

        self.bind(
            position=self.mark_view_dirty,
            target=self.mark_view_dirty,
            up=self.mark_view_dirty,
            fov=self.mark_view_dirty,
            near=self.mark_view_dirty,
            far=self.mark_view_dirty,
            ortho_size=self.mark_view_dirty,
            projection=self.mark_view_dirty,
        )



    def get_view_matrix(self) -> Matrix4:
        return Matrix4.look_at(
            self.position,
            self.target,
            self.up,
        )

    def get_projection_matrix(
        self,
        aspect: float,
    ) -> Matrix4:

        perspective = 1.0 if self.projection == "perspective" else 0.0

        if self.projection == "orthographic":
            right = self.ortho_size / 2.0
            left = -right
            top = right / aspect
            bottom = -top
        else:
            top = self.near * self.tan_half_fov()
            bottom = -top
            right = top * aspect
            left = -right

        return Matrix4.view_clip(
            left,
            right,
            bottom,
            top,
            self.near,
            self.far,
            perspective
        )

    def tan_half_fov(self) -> float:
        return math.tan(
            math.radians(self.fov) / 2.0
        )

    def set_look_at(
        self,
        position: Vector3,
        target: Vector3,
        up: Vector3 | None = None,
    ) -> None:
        self.position = position
        self.target = target

        if up is not None:
            self.up = up

    def mark_view_dirty(self, *_) -> None:
        self.dispatch("on_view_dirty")

    def on_view_dirty(self) -> None:
        pass


