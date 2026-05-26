# kivyfn/three/math/quaternion.py

from __future__ import annotations

import math

from kivyfn.three.math.matrix import Matrix3, Matrix4


class Quaternion:



    def __repr__(self) -> str:
        return (
            f"Quaternion("
            f"x={self.x}, "
            f"y={self.y}, "
            f"z={self.z}, "
            f"w={self.w})"
        )

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        w: float = 1.0,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    @classmethod
    def identity(cls) -> Quaternion:
        return cls()

    @classmethod
    def from_matrix3(cls, matrix: Matrix3) -> Quaternion:
        m = matrix.values.flatten()

        m00, m01, m02 = m[0], m[1], m[2]
        m10, m11, m12 = m[3], m[4], m[5]
        m20, m21, m22 = m[6], m[7], m[8]

        trace = m00 + m11 + m22

        if trace > 0.0:
            scale = math.sqrt(trace + 1.0) * 2.0
            w = 0.25 * scale
            x = (m21 - m12) / scale
            y = (m02 - m20) / scale
            z = (m10 - m01) / scale

        elif m00 > m11 and m00 > m22:
            scale = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
            w = (m21 - m12) / scale
            x = 0.25 * scale
            y = (m01 + m10) / scale
            z = (m02 + m20) / scale

        elif m11 > m22:
            scale = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
            w = (m02 - m20) / scale
            x = (m01 + m10) / scale
            y = 0.25 * scale
            z = (m12 + m21) / scale

        else:
            scale = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
            w = (m10 - m01) / scale
            x = (m02 + m20) / scale
            y = (m12 + m21) / scale
            z = 0.25 * scale

        return cls(x, y, z, w).normalize()

    @classmethod
    def from_matrix4(cls, matrix: Matrix4) -> Quaternion:
        return cls.from_matrix3(
            Matrix3(matrix.values[:3, :3])
        )

    @classmethod
    def from_axis_angle(
        cls,
        axis,
        angle_degrees: float,
    ) -> Quaternion:
        axis = axis.normalize()

        half_angle = math.radians(angle_degrees) / 2.0

        sine = math.sin(half_angle)
        cosine = math.cos(half_angle)

        return cls(
            axis.x * sine,
            axis.y * sine,
            axis.z * sine,
            cosine,
        ).normalize()

    # =================================== #
    # Operations
    # =================================== #
    def __mul__(
        self,
        other: Quaternion | float,
    ) -> Quaternion:
        if isinstance(other, (int, float)):
            return Quaternion(
                self.x * other,
                self.y * other,
                self.z * other,
                self.w * other,
            )

        if not isinstance(other, Quaternion):
            return NotImplemented

        a = self
        b = other

        return Quaternion(
            x=a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            y=a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
            z=a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
            w=a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        )

    def __rmul__(
        self,
        other: float,
    ) -> Quaternion:
        if isinstance(other, (int, float)):
            return self * other

        return NotImplemented

    def __truediv__(
        self,
        value: float,
    ) -> Quaternion:
        if value == 0.0:
            raise ZeroDivisionError("Cannot divide quaternion by zero.")

        return Quaternion(
            self.x / value,
            self.y / value,
            self.z / value,
            self.w / value,
        )

    def __neg__(self) -> Quaternion:
        return Quaternion(
            -self.x,
            -self.y,
            -self.z,
            -self.w,
        )

    def dot(
        self,
        other: Quaternion,
    ) -> float:
        return (
            self.x * other.x
            + self.y * other.y
            + self.z * other.z
            + self.w * other.w
        )

    def magnitude(self) -> float:
        return math.sqrt(self.dot(self))

    def normalize(self) -> Quaternion:
        magnitude = self.magnitude()

        if magnitude == 0.0:
            return Quaternion.identity()

        return self / magnitude

    def conjugate(self) -> Quaternion:
        return Quaternion(
            -self.x,
            -self.y,
            -self.z,
            self.w,
        )

    def inverse(self) -> Quaternion:
        length_squared = self.dot(self)

        if length_squared == 0.0:
            return Quaternion.identity()

        return self.conjugate() / length_squared

    def copy(self) -> Quaternion:
        return Quaternion(
            self.x,
            self.y,
            self.z,
            self.w,
        )

    # =================================== #
    # Conversions
    # =================================== #
    def to_matrix3(self) -> Matrix3:
        q = self.normalize()

        x = q.x
        y = q.y
        z = q.z
        w = q.w

        x2 = x + x
        y2 = y + y
        z2 = z + z

        xx = x * x2
        xy = x * y2
        xz = x * z2

        yy = y * y2
        yz = y * z2
        zz = z * z2

        wx = w * x2
        wy = w * y2
        wz = w * z2

        return Matrix3([
            [1.0 - (yy + zz), xy - wz, xz + wy],
            [xy + wz, 1.0 - (xx + zz), yz - wx],
            [xz - wy, yz + wx, 1.0 - (xx + yy)],
        ])

    def to_matrix4(self) -> Matrix4:
        matrix = Matrix4.identity()
        matrix.values[:3, :3] = self.to_matrix3().values
        return matrix

    def to_axis_angle(self) -> tuple[float, float, float, float]:
        q = self.normalize()

        w = max(-1.0, min(1.0, q.w))
        angle = 2.0 * math.degrees(math.acos(w))

        scale = math.sqrt(max(0.0, 1.0 - w * w))

        if scale < 1e-4:
            return (1.0, 0.0, 0.0, angle)

        return (
            q.x / scale,
            q.y / scale,
            q.z / scale,
            angle,
        )

    def tolist(self) -> list[float]:
        return [self.x, self.y, self.z, self.w]

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        yield self.w


