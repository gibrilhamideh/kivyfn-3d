
# kivyfn/three/animations/clip.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.animations.channel import AnimationChannel


@dataclass(frozen=True, slots=True)
class AnimationClip:
    name: str
    channels: tuple[AnimationChannel, ...] = field(default_factory=tuple)
    duration: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "duration",
            max(
                (channel.sampler.duration for channel in self.channels),
                default=0.0,
            ),
        )

