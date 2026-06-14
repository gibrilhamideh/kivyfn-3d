# kivyfn/three/math/matrix.py

from __future__ import annotations

import numpy as np

from kivy.graphics.transformation import Matrix
from kivyfn.three.math.vector import Vector3


class Matrix3:
    def __init__(self, values=None):
        if values is None:
            self.values = np.identity(3, dtype=np.float32)
        else:
            self.values = np.array(values, dtype=np.float32).reshape((3, 3))

    @classmethod
    def identity(cls) -> Matrix3:
        return cls()

    def transpose(self) -> Matrix3:
        return Matrix3(self.values.T)

    def inverse(self) -> Matrix3:
        return Matrix3(np.linalg.inv(self.values))

    def tolist(self):
        return self.values.tolist()

    def to_matrix4(self) -> Matrix4:
        matrix = np.identity(4, dtype=np.float32)
        matrix[:3, :3] = self.values
        return Matrix4(matrix)

    def to_uniform(self) -> Matrix:
        return self.to_matrix4().to_uniform()

    def __matmul__(self, other: Matrix3) -> Matrix3:
        return Matrix3(self.values @ other.values)

    def __repr__(self) -> str:
        formatted = np.array2string(
            self.values,
            precision=3,
            suppress_small=True,
        )

        return f"Matrix3(\n{formatted}\n)"


class Matrix4:
    def __init__(self, values=None):
        if values is None:
            self.values = np.identity(4, dtype=np.float32)
        else:
            self.values = np.array(values, dtype=np.float32).reshape((4, 4))

    @classmethod
    def identity(cls) -> Matrix4:
        return cls()


    @classmethod
    def look_at(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
    ) -> Matrix4:
        forward = (target - eye).normalize()
        right = forward.cross(up).normalize()
        true_up = right.cross(forward).normalize()

        return cls([
            [right.x, right.y, right.z, -right.dot(eye)],
            [true_up.x, true_up.y, true_up.z, -true_up.dot(eye)],
            [-forward.x, -forward.y, -forward.z, forward.dot(eye)],
            [0.0, 0.0, 0.0, 1.0],
        ])

    @classmethod
    def view_clip(
        cls,
        left: float,
        right: float,
        bottom: float,
        top: float,
        near: float,
        far: float,
        perspective: float,
    ) -> Matrix4:
        if perspective == 0.0:
            return cls([
                [2.0 / (right - left), 0.0, 0.0, -(right + left) / (right - left)],
                [0.0, 2.0 / (top - bottom), 0.0, -(top + bottom) / (top - bottom)],
                [0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)],
                [0.0, 0.0, 0.0, 1.0],
            ])

        return cls([
            [(2.0 * near) / (right - left), 0.0, (right + left) / (right - left), 0.0],
            [0.0, (2.0 * near) / (top - bottom), (top + bottom) / (top - bottom), 0.0],
            [0.0, 0.0, -(far + near) / (far - near), -(2.0 * far * near) / (far - near)],
            [0.0, 0.0, -1.0, 0.0],
        ])

    def transpose(self) -> Matrix4:
        return Matrix4(self.values.T)

    def inverse(self) -> Matrix4:
        return Matrix4(np.linalg.inv(self.values))

    def compute_normal_matrix(self) -> Matrix3:
        rotation = self.values[:3, :3].astype(np.float64)
        normal = np.linalg.inv(rotation).T
        return Matrix3(normal.astype(np.float32))

    def transform_point(
        self,
        point: Vector3,
    ) -> Vector3:
        result = self.values @ np.array(
            [point.x, point.y, point.z, 1.0],
            dtype=np.float32,
        )

        w = float(result[3])

        if w != 0.0 and w != 1.0:
            result = result / w

        return Vector3(
            float(result[0]),
            float(result[1]),
            float(result[2]),
        )


    def transform_direction(
        self,
        direction: Vector3,
    ) -> Vector3:
        result = self.values @ np.array(
            [direction.x, direction.y, direction.z, 0.0],
            dtype=np.float32,
        )

        return Vector3(
            float(result[0]),
            float(result[1]),
            float(result[2]),
        )

    def tolist(self):
        return self.values.tolist()

    def to_uniform(self) -> Matrix:
        matrix = Matrix()
        matrix.set(
            array=self.values.T.tolist(),
        )
        return matrix

    def __matmul__(self, other: Matrix4) -> Matrix4:
        return Matrix4(self.values @ other.values)

    def __repr__(self) -> str:
        formatted = np.array2string(
            self.values,
            precision=3,
            suppress_small=True,
        )

        return f"Matrix4(\n{formatted}\n)"
