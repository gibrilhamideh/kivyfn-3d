# kivyfn/three/scene/view.py

from __future__ import annotations
from typing import Literal
import math
from kivy.graphics.transformation import Matrix
from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        OptionProperty,
)

from kivyfn.three.math.vector import Vector3
from kivyfn.three.graph.node import Node3D


class View(Node3D):

    position: Vector3 = ObjectProperty(None, allownone=True)
    target: Vector3 = ObjectProperty(None, allownone=True)
    up: Vector3 = ObjectProperty(None, allownone=True)

    fov: float = NumericProperty(45.0)
    near: float = NumericProperty(1.0)
    far: float = NumericProperty(1000.0)

    ortho_size: float = NumericProperty(20.0)
    perspective: int = NumericProperty(1.0)
    projection_type: Literal[
        "perspective",
        "orthographic"
        ] = OptionProperty("perspective", options=["perspective", "orthographic"])

    def __repr__(self) -> str:
        return (
            "View(\n"
            f"  name={self.name!r},\n"
            f"  projection_type={self.projection_type!r},\n"
            f"  fov={self.fov:.1f},\n"
            f"  position={self.position},\n"
            f"  target={self.target},\n"
            f"  up={self.up}\n"
            ")"
        )

    def __init__(
        self,
        name: str = "camera",
        position: Vector3 | None = None,
        target: Vector3 | None = None,
        up: Vector3 | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            **kwargs,
        )

        self.position = position or Vector3(0.0, 0.0, 10.0)
        self.target = target or Vector3.zero()
        self.up = up or Vector3(0.0, 1.0, 0.0)

    def on_projection_type(self, instance, value: str) -> None:
        """Automatically updates the matrix interpolator factor when projection style changes."""
        if value == "perspective":
            self.perspective = 1
        elif value == "orthographic":
            self.perspective = 0

    def get_view_matrix(self) -> Matrix:
        matrix = Matrix()
        return matrix.look_at(
            self.position.x,
            self.position.y,
            self.position.z,
            self.target.x,
            self.target.y,
            self.target.z,
            self.up.x,
            self.up.y,
            self.up.z,
        )

    def get_projection_matrix(
        self,
        aspect: float,
    ) -> Matrix:
        # Evaluate layout dimensions contextually depending on active matrix styling
        if self.perspective == 0.0:
            # Orthographic view frustum calculations based on world units
            right = self.ortho_size / 2.0
            left = -right
            top = right / aspect
            bottom = -top
        else:
            # Traditional Perspective field-of-view calculation
            top = self.near * self._tan_half_fov()
            bottom = -top
            right = top * aspect
            left = -right

        return Matrix().view_clip(
            left,
            right,
            bottom,
            top,
            self.near,
            self.far,
            self.perspective,
        )

    def _tan_half_fov(self) -> float:
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


