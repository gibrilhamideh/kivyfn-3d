# kivyfn/three/math/transform.py

from __future__ import annotations

import numpy as np

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion


class Transform:
    def __init__(
        self,
        translation=None,
        rotation=None,
        scale=None,
    ):
        self.translation = (
            translation
            or (0.0, 0.0, 0.0)
        )

        self.rotation = (
            rotation
            or Quaternion.identity()
        )

        self.scale = (
            scale
            or (1.0, 1.0, 1.0)
        )

    def to_matrix4(self) -> Matrix4:
        tx, ty, tz = self.translation
        sx, sy, sz = self.scale

        rotation_matrix = self.rotation.to_matrix3()

        scale_matrix = np.diag(
            [sx, sy, sz]
        ).astype(np.float32)

        matrix = np.identity(
            4,
            dtype=np.float32,
        )

        matrix[:3, :3] = (
            rotation_matrix.values @ scale_matrix
        )

        matrix[:3, 3] = [
            tx,
            ty,
            tz,
        ]

        return Matrix4(matrix)

    def __repr__(self) -> str:
        return (
            f"Transform("
            f"translation={self.translation}, "
            f"rotation={self.rotation}, "
            f"scale={self.scale})"
        )
