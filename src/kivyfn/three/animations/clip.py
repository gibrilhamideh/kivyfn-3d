
# kivyfn/three/animations/clip.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.animations.channel import AnimationChannel


@dataclass(frozen=True, slots=True)
class AnimationClip:
    name: str
    channels: tuple[AnimationChannel, ...] = field(default_factory=tuple)

    @property
    def duration(self) -> float:
        if not self.channels:
            return 0.0

        return max(
            channel.sampler.duration
            for channel in self.channels
        )
