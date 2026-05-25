# kivyfn/three/scene/camera.py

from __future__ import annotations
from typing import Literal
import math
from kivy.graphics.transformation import Matrix
from kivy.properties import NumericProperty, ObjectProperty, OptionProperty

from kivyfn.three.math.vector import Vector3
from kivyfn.three.scene.node import Node3D


class Camera(Node3D):
    # Kivy properties to allow reactive auto-binding inside the Scene class
    eye = ObjectProperty(None, allownone=True)
    target = ObjectProperty(None, allownone=True)
    up = ObjectProperty(None, allownone=True)

    fov = NumericProperty(45.0)
    near = NumericProperty(1.0)
    far = NumericProperty(1000.0)

    ortho_size = NumericProperty(20.0)
    perspective: int = NumericProperty(1)
    projection_type: Literal[
        "perspective",
        "orthographic"
        ] = OptionProperty("perspective", options=["perspective", "orthographic"])

    def __init__(
        self,
        name: str = "camera",
        eye: Vector3 | None = None,
        target: Vector3 | None = None,
        up: Vector3 | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            **kwargs,
        )

        self.eye = eye or Vector3(0.0, 0.0, 10.0)
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
            self.eye.x,
            self.eye.y,
            self.eye.z,
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
        eye: Vector3,
        target: Vector3,
        up: Vector3 | None = None,
    ) -> None:
        self.eye = eye
        self.target = target

        if up is not None:
            self.up = up

    def __repr__(self) -> str:
        return (
            f"Camera("
            f"name={self.name!r}, "
            f"projection_type={self.projection_type!r}, "
            f"eye={self.eye}, "
            f"target={self.target})"
        )
