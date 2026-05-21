# kivyfn/three/primitive/cube.py

from __future__ import annotations

from kivyfn.three.render.material import Material
from kivyfn.three.render.meshdata import MeshData
from kivyfn.three.scene.object3d import Object3D


class Cube(Object3D):
    def __init__(
        self,
        size: float = 1.0,
        material: Material | None = None,
        **kwargs,
    ):
        half = size / 2.0

        vertices = [
            # Front
            -half, -half,  half,   0, 0, 1,   0, 0,
             half, -half,  half,   0, 0, 1,   1, 0,
             half,  half,  half,   0, 0, 1,   1, 1,
            -half,  half,  half,   0, 0, 1,   0, 1,

            # Back
             half, -half, -half,   0, 0, -1,  0, 0,
            -half, -half, -half,   0, 0, -1,  1, 0,
            -half,  half, -half,   0, 0, -1,  1, 1,
             half,  half, -half,   0, 0, -1,  0, 1,

            # Left
            -half, -half, -half,  -1, 0, 0,   0, 0,
            -half, -half,  half,  -1, 0, 0,   1, 0,
            -half,  half,  half,  -1, 0, 0,   1, 1,
            -half,  half, -half,  -1, 0, 0,   0, 1,

            # Right
             half, -half,  half,   1, 0, 0,   0, 0,
             half, -half, -half,   1, 0, 0,   1, 0,
             half,  half, -half,   1, 0, 0,   1, 1,
             half,  half,  half,   1, 0, 0,   0, 1,

            # Top
            -half,  half,  half,   0, 1, 0,   0, 0,
             half,  half,  half,   0, 1, 0,   1, 0,
             half,  half, -half,   0, 1, 0,   1, 1,
            -half,  half, -half,   0, 1, 0,   0, 1,

            # Bottom
            -half, -half, -half,   0, -1, 0,  0, 0,
             half, -half, -half,   0, -1, 0,  1, 0,
             half, -half,  half,   0, -1, 0,  1, 1,
            -half, -half,  half,   0, -1, 0,  0, 1,
        ]

        indices = [
             0,  1,  2,   2,  3,  0,
             4,  5,  6,   6,  7,  4,
             8,  9, 10,  10, 11,  8,
            12, 13, 14,  14, 15, 12,
            16, 17, 18,  18, 19, 16,
            20, 21, 22,  22, 23, 20,
        ]

        mesh_data = MeshData(
            vertices=vertices,
            indices=indices,
        )

        super().__init__(
            mesh_data=mesh_data,
            material=material or Material(),
            **kwargs,
        )
