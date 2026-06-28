# kivyfn/three/parsers/glb/scene.py

from __future__ import annotations

from dataclasses import dataclass, field

from kivyfn.three.parsers.glb.node import GlbNode


@dataclass(slots=True)
class GlbScene:
    name: str = ""
    roots: list[GlbNode] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.roots

    def __bool__(self) -> bool:
        return bool(self.roots)
