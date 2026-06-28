# kivyfn/three/animations/action.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.animations.clip import AnimationClip


@dataclass(slots=True)
class AnimationAction:
    clip: AnimationClip
    time: float = 0.0
    speed: float = 1.0
    loop: bool = False
    playing: bool = True

    def reset(self) -> None:
        self.time = 0.0
        self.playing = True

    def stop(self) -> None:
        self.playing = False
