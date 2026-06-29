# kivyfn/three/animations/interpolation.py

from __future__ import annotations

from kivyfn.three.animations.types import AnimationWeights
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector2, Vector3, Vector4


class AnimationInterpolation:

    @staticmethod
    def float(
        start: float,
        end: float,
        alpha: float,
    ) -> float:
        return start + ((end - start) * alpha)

    @staticmethod
    def vector2(
        start: Vector2,
        end: Vector2,
        alpha: float,
    ) -> Vector2:
        return start.lerp(end, alpha)

    @staticmethod
    def vector3(
        start: Vector3,
        end: Vector3,
        alpha: float,
    ) -> Vector3:
        return start.lerp(end, alpha)

    @staticmethod
    def vector4(
        start: Vector4,
        end: Vector4,
        alpha: float,
    ) -> Vector4:
        return start.lerp(end, alpha)

    @staticmethod
    def quaternion(
        start: Quaternion,
        end: Quaternion,
        alpha: float,
    ) -> Quaternion:
        return start.slerp(end, alpha)

    @staticmethod
    def weights(
        start: AnimationWeights,
        end: AnimationWeights,
        alpha: float,
    ) -> AnimationWeights:
        return tuple(
            float(a) + ((float(b) - float(a)) * alpha)
            for a, b in zip(start, end)
        )
