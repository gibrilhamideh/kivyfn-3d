# kivyfn/three/light/base.py

from __future__ import annotations

from kivyfn.three.scene.node import Node3D


class Light3D(Node3D):


    def __repr__(self) -> str:
        return (
            "Light3D(\n"
            f"    name={self.name!r},\n"
            f"    color={self.color},\n"
            f"    intensity={self.intensity},\n"
            ")"
        )

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


