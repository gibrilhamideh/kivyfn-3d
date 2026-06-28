# kivyfn/three/parsers/glb/skin.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.math.matrix import Matrix4


@dataclass(frozen=True, slots=True)
class GlbSkin:
    name: str
    joint_indices: tuple[int, ...]
    inverse_bind_matrices: tuple[Matrix4, ...]
