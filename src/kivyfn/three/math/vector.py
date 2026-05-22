# kivyfn/three/math/vector.py

from __future__ import annotations

import math


EPSILON = 1e-8


class Vector3:
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def zero(cls) -> Vector3:
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def one(cls) -> Vector3:
        return cls(1.0, 1.0, 1.0)

    @property
    def length(self) -> float:
        return math.sqrt(
            self.x * self.x +
            self.y * self.y +
            self.z * self.z
        )

    @property
    def magnitude(self) -> float:
        return self.length

    def normalize(self) -> Vector3:
        length = self.length

        if length < EPSILON:
            return Vector3.zero()

        return Vector3(
            self.x / length,
            self.y / length,
            self.z / length,
        )

    def dot(self, other: Vector3) -> float:
        return (
            self.x * other.x +
            self.y * other.y +
            self.z * other.z
        )

    def cross(self, other: Vector3) -> Vector3:
        return Vector3(
            (self.y * other.z) - (self.z * other.y),
            (self.z * other.x) - (self.x * other.z),
            (self.x * other.y) - (self.y * other.x),
        )

    def scale(self, scalar: float) -> Vector3:
        return Vector3(
            self.x * scalar,
            self.y * scalar,
            self.z * scalar,
        )

    def lerp(
        self,
        other: Vector3,
        t: float,
    ) -> Vector3:
        return Vector3(
            self.x + ((other.x - self.x) * t),
            self.y + ((other.y - self.y) * t),
            self.z + ((other.z - self.z) * t),
        )

    def rotate(
        self,
        axis: Vector3,
        angle_radians: float,
    ) -> Vector3:
        axis = axis.normalize()

        cosine = math.cos(angle_radians)
        sine = math.sin(angle_radians)

        part1 = self.scale(cosine)

        part2 = axis.cross(self).scale(sine)

        part3 = axis.scale(
            axis.dot(self) * (1.0 - cosine)
        )

        return part1 + part2 + part3

    @staticmethod
    def clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        return max(
            minimum,
            min(maximum, value),
        )

    @staticmethod
    def reorthonormalize(
        forward: Vector3,
        up: Vector3,
    ):
        forward = forward.normalize()

        right = (
            forward.cross(up)
            .normalize()
        )

        if right.length < EPSILON:
            right = Vector3(1.0, 0.0, 0.0)

        up = (
            right.cross(forward)
            .normalize()
        )

        return (
            forward,
            right,
            up,
        )

    def tolist(self) -> list[float]:
        return [
            self.x,
            self.y,
            self.z,
        ]

    def copy(self) -> Vector3:
        return Vector3(
            self.x,
            self.y,
            self.z,
        )

    def __add__(
        self,
        other: Vector3,
    ) -> Vector3:
        return Vector3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __sub__(
        self,
        other: Vector3,
    ) -> Vector3:
        return Vector3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __mul__(
        self,
        scalar: float,
    ) -> Vector3:
        return self.scale(scalar)

    def __truediv__(
        self,
        scalar: float,
    ) -> Vector3:
        if abs(scalar) < EPSILON:
            raise ZeroDivisionError(
                "Cannot divide Vector3 by zero."
            )

        return Vector3(
            self.x / scalar,
            self.y / scalar,
            self.z / scalar,
        )

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __repr__(self) -> str:
        return (
            f"Vector3("
            f"x={self.x}, "
            f"y={self.y}, "
            f"z={self.z})"
        )
