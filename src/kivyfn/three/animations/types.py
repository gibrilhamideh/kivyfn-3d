# kivyfn/three/animations/types.py

from __future__ import annotations

from typing import Literal, Protocol, Any
from collections.abc import Callable

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector2, Vector3, Vector4


AnimationPath = Literal[
    "translation",
    "rotation",
    "scale",
    "weights",
]

InterpolationMode = Literal[
    "step",
    "linear",
    "cubic_spline",
]

AnimationTarget = int | str

AnimationWeights = tuple[float, ...]



AnimationValue = (
    float
    | Vector2
    | Vector3
    | Vector4
    | Quaternion
    | AnimationWeights
)

AnimationInterpolator = Callable[
    [Any, Any, float],
    AnimationValue,
]

AnimationApplier = Callable[
    [Any, Any],
    None,
]

class AnimationTargetProtocol(Protocol):
    def set_translation(self, value: Vector3) -> None:
        ...

    def set_rotation(self, value: Quaternion) -> None:
        ...

    def set_scale(self, value: Vector3) -> None:
        ...

    def set_weights(self, value: tuple[float, ...]) -> None:
        ...
