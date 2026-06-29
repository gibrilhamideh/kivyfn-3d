# kivyfn/three/animations/channel.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.graph.node import Node3D
from kivyfn.three.animations.sampler import AnimationSampler
from kivyfn.three.animations.types import (
    AnimationApplier,
    AnimationPath,
    AnimationTarget,
)


@dataclass(frozen=True, slots=True)
class AnimationChannel:
    target: AnimationTarget
    path: AnimationPath
    sampler: AnimationSampler


@dataclass(slots=True)
class BoundAnimationChannel:
    node: Node3D
    path: AnimationPath
    sampler: AnimationSampler
    applier: AnimationApplier
