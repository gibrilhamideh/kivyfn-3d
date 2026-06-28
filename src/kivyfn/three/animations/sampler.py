# kivyfn/three/animations/sampler.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.animations.keyframe import AnimationKeyframe
from kivyfn.three.animations.types import (
    AnimationValue,
    InterpolationMode,
)
from kivyfn.three.animations.utility import (
    copy_animation_value,
    interpolate_animation_value,
)


@dataclass(frozen=True, slots=True)
class AnimationSampler:
    keyframes: tuple[AnimationKeyframe, ...]
    interpolation: InterpolationMode = "linear"

    @property
    def duration(self) -> float:
        if not self.keyframes:
            return 0.0

        return self.keyframes[-1].time

    def sample(
        self,
        time: float,
    ) -> AnimationValue:
        if not self.keyframes:
            raise ValueError(
                "Cannot sample animation sampler with no keyframes."
            )

        if time <= self.keyframes[0].time:
            return copy_animation_value(
                self.keyframes[0].value
            )

        if time >= self.keyframes[-1].time:
            return copy_animation_value(
                self.keyframes[-1].value
            )

        previous = self.keyframes[0]

        for current in self.keyframes[1:]:
            if time <= current.time:
                if self.interpolation == "step":
                    return copy_animation_value(
                        previous.value
                    )

                alpha = (
                    (time - previous.time)
                    / (current.time - previous.time)
                )

                return interpolate_animation_value(
                    previous.value,
                    current.value,
                    alpha,
                )

            previous = current

        return copy_animation_value(
            self.keyframes[-1].value
        )
