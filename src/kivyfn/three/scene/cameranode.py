# kivyfn/three/scene/cameranode.py

from __future__ import annotations

from kivy.graphics.transformation import Matrix
from kivy.properties import NumericProperty, ObjectProperty

from kivyfn.three.math.vector import Vector3
from kivyfn.three.scene.node import Node3D


class CameraNode(Node3D):
    eye = ObjectProperty(None, allownone=True)
    target = ObjectProperty(None, allownone=True)
    up = ObjectProperty(None, allownone=True)

    fov_y_degrees = NumericProperty(45.0)
    near = NumericProperty(1.0)
    far = NumericProperty(1000.0)
    perspective = NumericProperty(1.0)

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
        import math

        return math.tan(
            math.radians(self.fov_y_degrees) / 2.0
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
            f"CameraNode("
            f"name={self.name!r}, "
            f"eye={self.eye}, "
            f"target={self.target})"
        )
