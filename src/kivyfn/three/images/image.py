# kivyfn/three/images/image.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Image:
    width: int
    height: int
    pixels: bytes
    channels: int = 4

    @property
    def size(
        self,
    ) -> tuple[int, int]:
        return self.width, self.height
