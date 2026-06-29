# kivyfn/three/math/matrix.py

from __future__ import annotations

import numpy as np
from kivy.graphics.transformation import Matrix

from kivyfn.three.math.vector import Vector3


class Matrix3:
    __slots__ = ("values",)

    _IDENTITY_VALUES = np.identity(
        3,
        dtype=np.float32,
    )

    def __init__(
        self,
        values=None,
    ) -> None:
        if values is None:
            self.values = np.identity(
                3,
                dtype=np.float32,
            )
        else:
            self.values = np.array(
                values,
                dtype=np.float32,
                copy=True,
            ).reshape((3, 3))

    @classmethod
    def identity(
        cls,
    ) -> Matrix3:
        return cls()

    @classmethod
    def empty(
        cls,
    ) -> Matrix3:
        matrix = cls.__new__(cls)
        matrix.values = np.empty(
            (3, 3),
            dtype=np.float32,
        )
        return matrix

    def copy(
        self,
    ) -> Matrix3:
        return Matrix3(
            self.values,
        )

    # =================================== #
    # Assignment
    # =================================== #

    def set_identity(
        self,
    ) -> Matrix3:
        np.copyto(
            self.values,
            self._IDENTITY_VALUES,
        )
        return self

    def set_from(
        self,
        other: Matrix3,
    ) -> Matrix3:
        np.copyto(
            self.values,
            other.values,
        )
        return self

    def set_values(
        self,
        values,
    ) -> Matrix3:
        self.values[...] = np.asarray(
            values,
            dtype=np.float32,
        ).reshape((3, 3))
        return self

    # =================================== #
    # In-place Operations
    # =================================== #

    def multiply_by(
        self,
        other: Matrix3,
    ) -> Matrix3:
        result = self.values @ other.values
        self.values[...] = result
        return self

    def premultiply_by(
        self,
        other: Matrix3,
    ) -> Matrix3:
        result = other.values @ self.values
        self.values[...] = result
        return self

    def multiply_from(
        self,
        left: Matrix3,
        right: Matrix3,
    ) -> Matrix3:
        if self is left or self is right:
            result = left.values @ right.values
            self.values[...] = result
            return self

        np.matmul(
            left.values,
            right.values,
            out=self.values,
        )
        return self

    def inverse_by(
        self,
    ) -> Matrix3:
        self.values[...] = np.linalg.inv(
            self.values,
        ).astype(
            np.float32,
            copy=False,
        )
        return self

    def inverse_from(
        self,
        other: Matrix3,
    ) -> Matrix3:
        if self is other:
            return self.inverse_by()

        self.values[...] = np.linalg.inv(
            other.values,
        ).astype(
            np.float32,
            copy=False,
        )
        return self

    def transpose_by(
        self,
    ) -> Matrix3:
        self.values[...] = self.values.T.copy()
        return self

    def transpose_from(
        self,
        other: Matrix3,
    ) -> Matrix3:
        if self is other:
            return self.transpose_by()

        self.values[...] = other.values.T
        return self

    def normal_from_matrix4(
        self,
        matrix: Matrix4,
    ) -> Matrix3:
        rotation = matrix.values[:3, :3].astype(
            np.float64,
            copy=False,
        )

        normal = np.linalg.inv(
            rotation,
        ).T

        self.values[...] = normal.astype(
            np.float32,
            copy=False,
        )
        return self

    # =================================== #
    # Non-mutating API
    # =================================== #

    def transpose(
        self,
    ) -> Matrix3:
        return Matrix3(
            self.values.T,
        )

    def inverse(
        self,
    ) -> Matrix3:
        return Matrix3(
            np.linalg.inv(
                self.values,
            )
        )

    def tolist(
        self,
    ) -> list[list[float]]:
        return self.values.tolist()

    def to_matrix4(
        self,
    ) -> Matrix4:
        matrix = Matrix4.identity()
        matrix.values[:3, :3] = self.values
        return matrix

    def to_uniform(
        self,
    ) -> Matrix:
        return self.to_matrix4().to_uniform()

    def __matmul__(
        self,
        other: Matrix3,
    ) -> Matrix3:
        return Matrix3(
            self.values @ other.values,
        )

    def __repr__(
        self,
    ) -> str:
        formatted = np.array2string(
            self.values,
            precision=3,
            suppress_small=True,
        )

        return f"Matrix3(\n{formatted}\n)"


class Matrix4:
    __slots__ = ("values",)

    _IDENTITY_VALUES = np.identity(
        4,
        dtype=np.float32,
    )

    def __init__(
        self,
        values=None,
    ) -> None:
        if values is None:
            self.values = np.identity(
                4,
                dtype=np.float32,
            )
        else:
            self.values = np.array(
                values,
                dtype=np.float32,
                copy=True,
            ).reshape((4, 4))

    @classmethod
    def identity(
        cls,
    ) -> Matrix4:
        return cls()

    @classmethod
    def empty(
        cls,
    ) -> Matrix4:
        matrix = cls.__new__(cls)
        matrix.values = np.empty(
            (4, 4),
            dtype=np.float32,
        )
        return matrix

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

        return cls(
            [
                [right.x, right.y, right.z, -right.dot(eye)],
                [true_up.x, true_up.y, true_up.z, -true_up.dot(eye)],
                [-forward.x, -forward.y, -forward.z, forward.dot(eye)],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )

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
            return cls(
                [
                    [
                        2.0 / (right - left),
                        0.0,
                        0.0,
                        -(right + left) / (right - left),
                    ],
                    [
                        0.0,
                        2.0 / (top - bottom),
                        0.0,
                        -(top + bottom) / (top - bottom),
                    ],
                    [
                        0.0,
                        0.0,
                        -2.0 / (far - near),
                        -(far + near) / (far - near),
                    ],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            )

        return cls(
            [
                [
                    (2.0 * near) / (right - left),
                    0.0,
                    (right + left) / (right - left),
                    0.0,
                ],
                [
                    0.0,
                    (2.0 * near) / (top - bottom),
                    (top + bottom) / (top - bottom),
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    -(far + near) / (far - near),
                    -(2.0 * far * near) / (far - near),
                ],
                [0.0, 0.0, -1.0, 0.0],
            ]
        )

    def copy(
        self,
    ) -> Matrix4:
        return Matrix4(
            self.values,
        )

    # =================================== #
    # Assignment
    # =================================== #

    def set_identity(
        self,
    ) -> Matrix4:
        np.copyto(
            self.values,
            self._IDENTITY_VALUES,
        )
        return self

    def set_from(
        self,
        other: Matrix4,
    ) -> Matrix4:
        np.copyto(
            self.values,
            other.values,
        )
        return self

    def set_values(
        self,
        values,
    ) -> Matrix4:
        self.values[...] = np.asarray(
            values,
            dtype=np.float32,
        ).reshape((4, 4))
        return self

    def set_from_translation(
        self,
        translation: Vector3,
    ) -> Matrix4:
        self.set_identity()

        self.values[0, 3] = translation.x
        self.values[1, 3] = translation.y
        self.values[2, 3] = translation.z

        return self

    def set_from_scale(
        self,
        scale: Vector3,
    ) -> Matrix4:
        values = self.values

        values[...] = 0.0
        values[0, 0] = scale.x
        values[1, 1] = scale.y
        values[2, 2] = scale.z
        values[3, 3] = 1.0

        return self

    # =================================== #
    # In-place Operations
    # =================================== #

    def multiply_by(
        self,
        other: Matrix4,
    ) -> Matrix4:
        result = self.values @ other.values
        self.values[...] = result
        return self

    def premultiply_by(
        self,
        other: Matrix4,
    ) -> Matrix4:
        result = other.values @ self.values
        self.values[...] = result
        return self

    def multiply_from(
        self,
        left: Matrix4,
        right: Matrix4,
    ) -> Matrix4:
        if self is left or self is right:
            result = left.values @ right.values
            self.values[...] = result
            return self

        np.matmul(
            left.values,
            right.values,
            out=self.values,
        )
        return self

    def inverse_by(
        self,
    ) -> Matrix4:
        self.values[...] = np.linalg.inv(
            self.values,
        ).astype(
            np.float32,
            copy=False,
        )
        return self

    def inverse_from(
        self,
        other: Matrix4,
    ) -> Matrix4:
        if self is other:
            return self.inverse_by()

        self.values[...] = np.linalg.inv(
            other.values,
        ).astype(
            np.float32,
            copy=False,
        )
        return self

    def transpose_by(
        self,
    ) -> Matrix4:
        self.values[...] = self.values.T.copy()
        return self

    def transpose_from(
        self,
        other: Matrix4,
    ) -> Matrix4:
        if self is other:
            return self.transpose_by()

        self.values[...] = other.values.T
        return self

    # =================================== #
    # Non-mutating API
    # =================================== #

    def transpose(
        self,
    ) -> Matrix4:
        return Matrix4(
            self.values.T,
        )

    def inverse(
        self,
    ) -> Matrix4:
        return Matrix4(
            np.linalg.inv(
                self.values,
            )
        )

    def to_normal_matrix(
        self,
    ) -> Matrix3:
        normal = Matrix3.empty()
        normal.normal_from_matrix4(
            self,
        )
        return normal

    def transform_point(
        self,
        point: Vector3,
    ) -> Vector3:
        values = self.values

        x = point.x
        y = point.y
        z = point.z

        rx = (
            values[0, 0] * x
            + values[0, 1] * y
            + values[0, 2] * z
            + values[0, 3]
        )
        ry = (
            values[1, 0] * x
            + values[1, 1] * y
            + values[1, 2] * z
            + values[1, 3]
        )
        rz = (
            values[2, 0] * x
            + values[2, 1] * y
            + values[2, 2] * z
            + values[2, 3]
        )
        rw = (
            values[3, 0] * x
            + values[3, 1] * y
            + values[3, 2] * z
            + values[3, 3]
        )

        if rw != 0.0 and rw != 1.0:
            inverse_w = 1.0 / rw

            rx *= inverse_w
            ry *= inverse_w
            rz *= inverse_w

        return Vector3(
            float(rx),
            float(ry),
            float(rz),
        )

    def transform_direction(
        self,
        direction: Vector3,
    ) -> Vector3:
        values = self.values

        x = direction.x
        y = direction.y
        z = direction.z

        return Vector3(
            float(
                values[0, 0] * x
                + values[0, 1] * y
                + values[0, 2] * z
            ),
            float(
                values[1, 0] * x
                + values[1, 1] * y
                + values[1, 2] * z
            ),
            float(
                values[2, 0] * x
                + values[2, 1] * y
                + values[2, 2] * z
            ),
        )

    def tolist(
        self,
    ) -> list[list[float]]:
        return self.values.tolist()

    def to_uniform(
        self,
    ) -> Matrix:
        matrix = Matrix()

        matrix.set(
            array=self.values.T.tolist(),
        )

        return matrix

    def __matmul__(
        self,
        other: Matrix4,
    ) -> Matrix4:
        return Matrix4(
            self.values @ other.values,
        )

    def __repr__(
        self,
    ) -> str:
        formatted = np.array2string(
            self.values,
            precision=3,
            suppress_small=True,
        )

        return f"Matrix4(\n{formatted}\n)"

