# kivyfn/three/light/base.py

from __future__ import annotations

from kivyfn.three.scene.node import Node3D


class Light3D(Node3D):
    def __init__(
        self,
        *,
        color: tuple[float, float, float] = (
            1.0,
            0.95,
            0.8,
        ),
        intensity: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.color = color
        self.intensity = intensity
