# kivyfn/three/animations/library.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.animations.controller import AnimationController


@dataclass(slots=True)
class AnimationLibrary:
    clips: dict[str, AnimationClip] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.clips

    def add(
        self,
        clip: AnimationClip,
    ) -> None:
        self.clips[clip.name] = clip

    def get(
        self,
        name: str,
    ) -> AnimationClip | None:
        return self.clips.get(name)

    def require(
        self,
        name: str,
    ) -> AnimationClip:
        clip = self.get(name)

        if clip is None:
            raise ValueError(f"Animation clip not found: {name!r}")

        return clip

    def names(self) -> list[str]:
        return list(self.clips)

    def bind(
        self,
        binding: AnimationBinding,
    ) -> AnimationController:
        return AnimationController(
            binding=binding,
            clips=self.clips,
        )
