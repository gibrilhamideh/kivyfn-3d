# kivyfn/three/animations/channel.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.animations.sampler import AnimationSampler
from kivyfn.three.animations.types import AnimationPath, AnimationTarget


@dataclass(frozen=True, slots=True)
class AnimationChannel:
    target: AnimationTarget
    path: AnimationPath
    sampler: AnimationSampler
