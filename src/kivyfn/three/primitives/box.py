# kivyfn/three/primitives/box.py

from __future__ import annotations

import numpy as np

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D


class Box(Object3D):
    def __init__(
        self,
        width: float = 2.0,
        height: float = 1.0,
        depth: float = 1.0,
        material: Material | None = None,
        with_tangents: bool = True,
        **kwargs,
    ):
        hw = width / 2.0
        hh = height / 2.0
        hd = depth / 2.0

        vertices_with_tangents = np.array(
            [
                # Front
                -hw, -hh,  hd,   0,  0,  1,   0, 0,    1, 0,  0, 1,
                 hw, -hh,  hd,   0,  0,  1,   1, 0,    1, 0,  0, 1,
                 hw,  hh,  hd,   0,  0,  1,   1, 1,    1, 0,  0, 1,
                -hw,  hh,  hd,   0,  0,  1,   0, 1,    1, 0,  0, 1,

                # Back
                 hw, -hh, -hd,   0,  0, -1,   0, 0,   -1, 0,  0, 1,
                -hw, -hh, -hd,   0,  0, -1,   1, 0,   -1, 0,  0, 1,
                -hw,  hh, -hd,   0,  0, -1,   1, 1,   -1, 0,  0, 1,
                 hw,  hh, -hd,   0,  0, -1,   0, 1,   -1, 0,  0, 1,

                # Left
                -hw, -hh, -hd,  -1,  0,  0,   0, 0,    0, 0, -1, 1,
                -hw, -hh,  hd,  -1,  0,  0,   1, 0,    0, 0, -1, 1,
                -hw,  hh,  hd,  -1,  0,  0,   1, 1,    0, 0, -1, 1,
                -hw,  hh, -hd,  -1,  0,  0,   0, 1,    0, 0, -1, 1,

                # Right
                 hw, -hh,  hd,   1,  0,  0,   0, 0,    0, 0,  1, 1,
                 hw, -hh, -hd,   1,  0,  0,   1, 0,    0, 0,  1, 1,
                 hw,  hh, -hd,   1,  0,  0,   1, 1,    0, 0,  1, 1,
                 hw,  hh,  hd,   1,  0,  0,   0, 1,    0, 0,  1, 1,

                # Top
                -hw,  hh,  hd,   0,  1,  0,   0, 0,    1, 0,  0, 1,
                 hw,  hh,  hd,   0,  1,  0,   1, 0,    1, 0,  0, 1,
                 hw,  hh, -hd,   0,  1,  0,   1, 1,    1, 0,  0, 1,
                -hw,  hh, -hd,   0,  1,  0,   0, 1,    1, 0,  0, 1,

                # Bottom
                -hw, -hh, -hd,   0, -1,  0,   0, 0,    1, 0,  0, 1,
                 hw, -hh, -hd,   0, -1,  0,   1, 0,    1, 0,  0, 1,
                 hw, -hh,  hd,   0, -1,  0,   1, 1,    1, 0,  0, 1,
                -hw, -hh,  hd,   0, -1,  0,   0, 1,    1, 0,  0, 1,
            ],
            dtype=np.float32,
        )

        if with_tangents:
            vertices = vertices_with_tangents

            fmt = [
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
                (b"v_tangent", 4, "float"),
            ]

        else:
            vertices = vertices_with_tangents.reshape(
                -1,
                12,
            )[:, :8].reshape(-1)

            fmt = [
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
            ]

        indices = np.array(
            [
                 0,  1,  2,   2,  3,  0,
                 4,  5,  6,   6,  7,  4,
                 8,  9, 10,  10, 11,  8,
                12, 13, 14,  14, 15, 12,
                16, 17, 18,  18, 19, 16,
                20, 21, 22,  22, 23, 20,
            ],
            dtype=np.uint16,
        )

        geometry = Geometry(
            fmt=fmt,
            vertices=vertices,
            indices=indices,
            has_tangents=with_tangents,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )
