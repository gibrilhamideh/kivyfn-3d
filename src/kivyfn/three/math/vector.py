# kivyfn/three/math/vector.py

from __future__ import annotations

import math


EPSILON = 1e-8


class Vector2:
    __slots__ = ("x", "y")

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
    ):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return (
            f"Vector2("
            f"x={self.x}, "
            f"y={self.y})"
        )

    @classmethod
    def zero(cls) -> Vector2:
        return cls(0.0, 0.0)

    @classmethod
    def one(cls) -> Vector2:
        return cls(1.0, 1.0)

    @property
    def length(self) -> float:
        return math.sqrt(
            self.x * self.x +
            self.y * self.y
        )

    def rotate(
        self,
        angle_radians: float,
    ) -> Vector2:
        cosine = math.cos(angle_radians)
        sine = math.sin(angle_radians)

        return Vector2(
            (self.x * cosine) - (self.y * sine),
            (self.x * sine) + (self.y * cosine),
        )

    @property
    def magnitude(self) -> float:
        return self.length

    @property
    def yx(self) -> Vector2:
        return Vector2(self.y, self.x)

    def normalize(self) -> Vector2:
        length = self.length

        if length < EPSILON:
            return Vector2.zero()

        return Vector2(
            self.x / length,
            self.y / length,
        )

    def dot(self, other: Vector2) -> float:
        return (
            self.x * other.x +
            self.y * other.y
        )

    def scale(self, scalar: float) -> Vector2:
        return Vector2(
            self.x * scalar,
            self.y * scalar,
        )

    def lerp(
        self,
        other: Vector2,
        t: float,
    ) -> Vector2:
        return Vector2(
            self.x + ((other.x - self.x) * t),
            self.y + ((other.y - self.y) * t),
        )

    def tolist(self) -> list[float]:
        return [
            self.x,
            self.y,
        ]

    def copy(self) -> Vector2:
        return Vector2(
            self.x,
            self.y,
        )

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Vector2):
            return NotImplemented

        return (
            abs(self.x - other.x) <= EPSILON and
            abs(self.y - other.y) <= EPSILON
        )

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(
            self.x + other.x,
            self.y + other.y,
        )

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(
            self.x - other.x,
            self.y - other.y,
        )

    def __mul__(self, scalar: float) -> Vector2:
        return self.scale(scalar)

    def __rmul__(self, scalar: float) -> Vector2:
        return self.scale(scalar)

    def __truediv__(self, scalar: float) -> Vector2:
        if abs(scalar) < EPSILON:
            raise ZeroDivisionError(
                "Cannot divide Vector2 by zero."
            )

        return Vector2(
            self.x / scalar,
            self.y / scalar,
        )

    def __neg__(self) -> Vector2:
        return Vector2(
            -self.x,
            -self.y,
        )

    def __iter__(self):
        yield self.x
        yield self.y


class Vector3:
    __slots__ = ("x", "y", "z")

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self) -> str:
        return (
            f"Vector3("
            f"x={self.x}, "
            f"y={self.y}, "
            f"z={self.z})"
        )

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

    @property
    def xy(self) -> Vector2:
        return Vector2(self.x, self.y)

    @property
    def xz(self) -> Vector2:
        return Vector2(self.x, self.z)

    @property
    def yz(self) -> Vector2:
        return Vector2(self.y, self.z)

    @property
    def yx(self) -> Vector2:
        return Vector2(self.y, self.x)

    @property
    def zx(self) -> Vector2:
        return Vector2(self.z, self.x)

    @property
    def zy(self) -> Vector2:
        return Vector2(self.z, self.y)

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
        one_minus_cosine = 1.0 - cosine

        dot = (
            axis.x * self.x +
            axis.y * self.y +
            axis.z * self.z
        )

        cross_x = (
            axis.y * self.z -
            axis.z * self.y
        )

        cross_y = (
            axis.z * self.x -
            axis.x * self.z
        )

        cross_z = (
            axis.x * self.y -
            axis.y * self.x
        )

        return Vector3(
            (
                self.x * cosine
            ) + (
                cross_x * sine
            ) + (
                axis.x * dot * one_minus_cosine
            ),

            (
                self.y * cosine
            ) + (
                cross_y * sine
            ) + (
                axis.y * dot * one_minus_cosine
            ),

            (
                self.z * cosine
            ) + (
                cross_z * sine
            ) + (
                axis.z * dot * one_minus_cosine
            ),
        )

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

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Vector3):
            return NotImplemented

        return (
            abs(self.x - other.x) <= EPSILON and
            abs(self.y - other.y) <= EPSILON and
            abs(self.z - other.z) <= EPSILON
        )

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __mul__(self, scalar: float) -> Vector3:
        return self.scale(scalar)

    def __rmul__(self, scalar: float) -> Vector3:
        return self.scale(scalar)

    def __truediv__(self, scalar: float) -> Vector3:
        if abs(scalar) < EPSILON:
            raise ZeroDivisionError(
                "Cannot divide Vector3 by zero."
            )

        return Vector3(
            self.x / scalar,
            self.y / scalar,
            self.z / scalar,
        )

    def __neg__(self) -> Vector3:
        return Vector3(
            -self.x,
            -self.y,
            -self.z,
        )

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


class Vector4:
    __slots__ = ("x", "y", "z", "w")

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        w: float = 0.0,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __repr__(self) -> str:
        return (
            f"Vector4("
            f"x={self.x}, "
            f"y={self.y}, "
            f"z={self.z}, "
            f"w={self.w})"
        )

    @classmethod
    def zero(cls) -> Vector4:
        return cls(0.0, 0.0, 0.0, 0.0)

    @classmethod
    def one(cls) -> Vector4:
        return cls(1.0, 1.0, 1.0, 1.0)

    @property
    def length(self) -> float:
        return math.sqrt(
            self.x * self.x +
            self.y * self.y +
            self.z * self.z +
            self.w * self.w
        )

    @property
    def magnitude(self) -> float:
        return self.length

    @property
    def xy(self) -> Vector2:
        return Vector2(self.x, self.y)

    @property
    def xz(self) -> Vector2:
        return Vector2(self.x, self.z)

    @property
    def xw(self) -> Vector2:
        return Vector2(self.x, self.w)

    @property
    def yz(self) -> Vector2:
        return Vector2(self.y, self.z)

    @property
    def yw(self) -> Vector2:
        return Vector2(self.y, self.w)

    @property
    def zw(self) -> Vector2:
        return Vector2(self.z, self.w)

    @property
    def yx(self) -> Vector2:
        return Vector2(self.y, self.x)

    @property
    def zx(self) -> Vector2:
        return Vector2(self.z, self.x)

    @property
    def wx(self) -> Vector2:
        return Vector2(self.w, self.x)

    @property
    def zy(self) -> Vector2:
        return Vector2(self.z, self.y)

    @property
    def wy(self) -> Vector2:
        return Vector2(self.w, self.y)

    @property
    def wz(self) -> Vector2:
        return Vector2(self.w, self.z)

    @property
    def xyz(self) -> Vector3:
        return Vector3(self.x, self.y, self.z)

    @property
    def xyw(self) -> Vector3:
        return Vector3(self.x, self.y, self.w)

    @property
    def xzw(self) -> Vector3:
        return Vector3(self.x, self.z, self.w)

    @property
    def yzw(self) -> Vector3:
        return Vector3(self.y, self.z, self.w)

    @property
    def r(self) -> float:
        return self.x

    @property
    def g(self) -> float:
        return self.y

    @property
    def b(self) -> float:
        return self.z

    @property
    def a(self) -> float:
        return self.w

    @property
    def rg(self) -> Vector2:
        return Vector2(self.r, self.g)

    @property
    def rb(self) -> Vector2:
        return Vector2(self.r, self.b)

    @property
    def ra(self) -> Vector2:
        return Vector2(self.r, self.a)

    @property
    def gb(self) -> Vector2:
        return Vector2(self.g, self.b)

    @property
    def ga(self) -> Vector2:
        return Vector2(self.g, self.a)

    @property
    def ba(self) -> Vector2:
        return Vector2(self.b, self.a)

    @property
    def rgb(self) -> Vector3:
        return Vector3(
            self.r,
            self.g,
            self.b,
        )

    @property
    def rgba(self) -> Vector4:
        return Vector4(
            self.r,
            self.g,
            self.b,
            self.a,
        )


    def normalize(self) -> Vector4:
        length = self.length

        if length < EPSILON:
            return Vector4.zero()

        return Vector4(
            self.x / length,
            self.y / length,
            self.z / length,
            self.w / length,
        )

    def dot(self, other: Vector4) -> float:
        return (
            self.x * other.x +
            self.y * other.y +
            self.z * other.z +
            self.w * other.w
        )

    def scale(self, scalar: float) -> Vector4:
        return Vector4(
            self.x * scalar,
            self.y * scalar,
            self.z * scalar,
            self.w * scalar,
        )

    def lerp(
        self,
        other: Vector4,
        t: float,
    ) -> Vector4:
        return Vector4(
            self.x + ((other.x - self.x) * t),
            self.y + ((other.y - self.y) * t),
            self.z + ((other.z - self.z) * t),
            self.w + ((other.w - self.w) * t),
        )

    def tolist(self) -> list[float]:
        return [
            self.x,
            self.y,
            self.z,
            self.w,
        ]

    def copy(self) -> Vector4:
        return Vector4(
            self.x,
            self.y,
            self.z,
            self.w,
        )

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if not isinstance(other, Vector4):
            return NotImplemented

        return (
            abs(self.x - other.x) <= EPSILON and
            abs(self.y - other.y) <= EPSILON and
            abs(self.z - other.z) <= EPSILON and
            abs(self.w - other.w) <= EPSILON
        )


    def __add__(self, other: Vector4) -> Vector4:
        return Vector4(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
            self.w + other.w,
        )

    def __sub__(self, other: Vector4) -> Vector4:
        return Vector4(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
            self.w - other.w,
        )

    def __mul__(self, scalar: float) -> Vector4:
        return self.scale(scalar)

    def __rmul__(self, scalar: float) -> Vector4:
        return self.scale(scalar)

    def __truediv__(self, scalar: float) -> Vector4:
        if abs(scalar) < EPSILON:
            raise ZeroDivisionError(
                "Cannot divide Vector4 by zero."
            )

        return Vector4(
            self.x / scalar,
            self.y / scalar,
            self.z / scalar,
            self.w / scalar,
        )

    def __neg__(self) -> Vector4:
        return Vector4(
            -self.x,
            -self.y,
            -self.z,
            -self.w,
        )

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        yield self.w
