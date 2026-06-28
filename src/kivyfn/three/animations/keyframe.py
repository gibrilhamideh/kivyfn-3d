# kivyfn/three/animations/keyframe.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.animations.types import AnimationValue


@dataclass(frozen=True, slots=True)
class AnimationKeyframe:
    time: float
    value: AnimationValue

    def __post_init__(self) -> None:
        if self.time < 0.0:
            raise ValueError(
                f"Animation keyframe time cannot be negative: {self.time}"
            )
