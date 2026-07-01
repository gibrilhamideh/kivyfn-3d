# kivyfn/three/animations/channel.py

from __future__ import annotations
from typing import cast
from dataclasses import dataclass

from kivyfn.three.math.vector import Vector3
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.animations.sampler import AnimationSampler
from kivyfn.three.animations.types import (
    AnimationPath,
    AnimationTarget,
    AnimationTargetProtocol,
)


@dataclass(frozen=True, slots=True)
class AnimationChannel:
    target: AnimationTarget
    path: AnimationPath
    sampler: AnimationSampler


@dataclass(slots=True)
class BoundAnimationChannel:
    target: AnimationTargetProtocol
    path: AnimationPath
    sampler: AnimationSampler

    def apply(
        self,
        time: float,
    ) -> None:
        value = self.sampler.sample(
            time,
        )

        match self.path:
            case "translation":
                self.target.set_translation(
                    cast(
                        Vector3,
                        value,
                    )
                )

            case "rotation":
                self.target.set_rotation(
                    cast(
                        Quaternion,
                        value,
                    )
                )

            case "scale":
                self.target.set_scale(
                    cast(
                        Vector3,
                        value,
                    )
                )

            case "weights":
                self.target.set_weights(
                    cast(
                        tuple[float, ...],
                        value,
                    )
                )
