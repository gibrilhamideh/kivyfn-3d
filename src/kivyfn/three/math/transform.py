# kivyfn/three/math/transform.py

from __future__ import annotations

import numpy as np

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3


class Transform:

    def __repr__(self) -> str:
        return (
            "Transform(\n"
            f"  translation={self.translation},\n"
            f"  rotation={self.rotation},\n"
            f"  scale={self.scale}\n"
            ")"
        )


    def __init__(
        self,
        translation: Vector3 | None = None,
        rotation: Quaternion | None = None,
        scale: Vector3 | None = None,
    ):
        self.translation = translation or Vector3(0.0, 0.0, 0.0)
        self.rotation = rotation or Quaternion.identity()
        self.scale = scale or Vector3(1.0, 1.0, 1.0)

    def copy(self) -> Transform:
        return Transform(
            translation=self.translation.copy(),
            rotation=self.rotation.copy(),
            scale=self.scale.copy(),
        )

    # =================================== #
    # Translation
    # =================================== #
    def set_translation(
        self,
        translation: Vector3,
    ) -> None:
        self.translation = translation

    def translate_by(
        self,
        offset: Vector3,
    ) -> None:
        self.translation = self.translation + offset

    # =================================== #
    # Scale
    # =================================== #
    def set_scale(
        self,
        scale: Vector3,
    ) -> None:
        self.scale = scale

    def scale_by(
        self,
        factor: Vector3,
    ) -> None:
        self.scale = Vector3(
            self.scale.x * factor.x,
            self.scale.y * factor.y,
            self.scale.z * factor.z,
        )

    # =================================== #
    # Rotation
    # =================================== #
    def set_rotation(
        self,
        rotation: Quaternion,
    ) -> None:
        self.rotation = rotation.normalize()

    def rotate_by(
        self,
        angle_degrees: float,
        axis: Vector3,
    ) -> None:
        delta = Quaternion.from_axis_angle(
            axis,
            angle_degrees,
        )

        self.set_rotation(
            (delta * self.rotation).normalize()
        )

    # =================================== #
    # Matrix
    # =================================== #
    def to_matrix4(
        self,
        origin: Vector3 | None = None,
    ) -> Matrix4:
        rotation_matrix = self.rotation.to_matrix3()

        scale_matrix = np.diag(
            [
                self.scale.x,
                self.scale.y,
                self.scale.z,
            ]
        ).astype(np.float32)

        linear = rotation_matrix.values @ scale_matrix

        translation = np.array(
            [
                self.translation.x,
                self.translation.y,
                self.translation.z,
            ],
            dtype=np.float32,
        )

        if origin is not None:
            origin_values = np.array(
                [
                    origin.x,
                    origin.y,
                    origin.z,
                ],
                dtype=np.float32,
            )

            translation = (
                translation
                + origin_values
                - linear @ origin_values
            )

        matrix = np.identity(
            4,
            dtype=np.float32,
        )

        matrix[:3, :3] = linear
        matrix[:3, 3] = translation

        return Matrix4(matrix)




