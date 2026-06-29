# kivyfn/three/animations/sampler.py

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

from kivyfn.three.animations.keyframe import AnimationKeyframe
from kivyfn.three.animations.types import (
    AnimationInterpolator,
    AnimationValue,
    InterpolationMode,
)


@dataclass(frozen=True, slots=True)
class AnimationSampler:
    keyframes: tuple[AnimationKeyframe, ...]
    interpolation: InterpolationMode
    interpolator: AnimationInterpolator
    times: tuple[float, ...] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "times",
            tuple(
                keyframe.time
                for keyframe in self.keyframes
            ),
        )

    @property
    def duration(self) -> float:
        if not self.keyframes:
            return 0.0

        return self.keyframes[-1].time

    def sample(
        self,
        time: float,
    ) -> AnimationValue:
        keyframes = self.keyframes
        times = self.times

        if not keyframes:
            raise ValueError(
                "Cannot sample animation sampler with no keyframes."
            )

        if time <= times[0]:
            return keyframes[0].value

        if time >= times[-1]:
            return keyframes[-1].value

        index = bisect_left(
            times,
            time,
        )

        previous = keyframes[index - 1]
        current = keyframes[index]

        if self.interpolation == "step":
            return previous.value

        alpha = (
            (time - previous.time)
            / (current.time - previous.time)
        )

        return self.interpolator(
            previous.value,
            current.value,
            alpha,
        )
