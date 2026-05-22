# kivyfn/three/primitives/box.py

from __future__ import annotations

from kivyfn.three.render.material import Material
from kivyfn.three.render.geometry import Geometry
from kivyfn.three.scene.object3d import Object3D


class Box(Object3D):
    def __init__(
        self,
        width: float = 2.0,
        height: float = 1.0,
        depth: float = 1.0,
        material: Material | None = None,
        **kwargs,
    ):
        hw = width / 2.0
        hh = height / 2.0
        hd = depth / 2.0

        vertices = [
            # Front
            -hw, -hh,  hd,   0, 0, 1,   0, 0,
             hw, -hh,  hd,   0, 0, 1,   1, 0,
             hw,  hh,  hd,   0, 0, 1,   1, 1,
            -hw,  hh,  hd,   0, 0, 1,   0, 1,

            # Back
             hw, -hh, -hd,   0, 0, -1,  0, 0,
            -hw, -hh, -hd,   0, 0, -1,  1, 0,
            -hw,  hh, -hd,   0, 0, -1,  1, 1,
             hw,  hh, -hd,   0, 0, -1,  0, 1,

            # Left
            -hw, -hh, -hd,  -1, 0, 0,   0, 0,
            -hw, -hh,  hd,  -1, 0, 0,   1, 0,
            -hw,  hh,  hd,  -1, 0, 0,   1, 1,
            -hw,  hh, -hd,  -1, 0, 0,   0, 1,

            # Right
             hw, -hh,  hd,   1, 0, 0,   0, 0,
             hw, -hh, -hd,   1, 0, 0,   1, 0,
             hw,  hh, -hd,   1, 0, 0,   1, 1,
             hw,  hh,  hd,   1, 0, 0,   0, 1,

            # Top
            -hw,  hh,  hd,   0, 1, 0,   0, 0,
             hw,  hh,  hd,   0, 1, 0,   1, 0,
             hw,  hh, -hd,   0, 1, 0,   1, 1,
            -hw,  hh, -hd,   0, 1, 0,   0, 1,

            # Bottom
            -hw, -hh, -hd,   0, -1, 0,  0, 0,
             hw, -hh, -hd,   0, -1, 0,  1, 0,
             hw, -hh,  hd,   0, -1, 0,  1, 1,
            -hw, -hh,  hd,   0, -1, 0,  0, 1,
        ]

        indices = [
             0,  1,  2,   2,  3,  0,
             4,  5,  6,   6,  7,  4,
             8,  9, 10,  10, 11,  8,
            12, 13, 14,  14, 15, 12,
            16, 17, 18,  18, 19, 16,
            20, 21, 22,  22, 23, 20,
        ]

        geometry = Geometry(
            vertices=vertices,
            indices=indices,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )
