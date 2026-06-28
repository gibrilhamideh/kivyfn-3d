# kivyfn/three/animations/utility.py

from __future__ import annotations

from kivyfn.three.animations.types import AnimationValue
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector2, Vector3, Vector4


def interpolate_animation_value(
    start: AnimationValue,
    end: AnimationValue,
    alpha: float,
) -> AnimationValue:
    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
        return float(start) + ((float(end) - float(start)) * alpha)

    if isinstance(start, Vector2) and isinstance(end, Vector2):
        return start.lerp(end, alpha)

    if isinstance(start, Vector3) and isinstance(end, Vector3):
        return start.lerp(end, alpha)

    if isinstance(start, Vector4) and isinstance(end, Vector4):
        return start.lerp(end, alpha)

    if isinstance(start, Quaternion) and isinstance(end, Quaternion):
        return start.slerp(end, alpha)

    if isinstance(start, tuple) and isinstance(end, tuple):
        if len(start) != len(end):
            raise TypeError(
                "Cannot interpolate animation weight tuples with different lengths."
            )

        return tuple(
            float(a) + ((float(b) - float(a)) * alpha)
            for a, b in zip(start, end)
        )

    raise TypeError(
        f"Cannot interpolate animation values: "
        f"{type(start).__name__} -> {type(end).__name__}"
    )


def copy_animation_value(
    value: AnimationValue,
) -> AnimationValue:
    if isinstance(value, (int, float)):
        return value

    if isinstance(value, tuple):
        return tuple(float(item) for item in value)

    if isinstance(value, (Vector2, Vector3, Vector4, Quaternion)):
        return value.copy()

    raise TypeError(
        f"Cannot copy animation value: {type(value).__name__}"
    )
