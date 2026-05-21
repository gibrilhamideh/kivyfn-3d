# kivyfn/three/primitives/cone.py

from __future__ import annotations

import math

from kivyfn.three.render.material import Material
from kivyfn.three.render.meshdata import MeshData
from kivyfn.three.scene.object3d import Object3D


class Cone(Object3D):
    def __init__(
        self,
        radius: float = 0.5,
        height: float = 1.0,
        segments: int = 32,
        material: Material | None = None,
        **kwargs,
    ):
        half_height = height / 2.0

        vertices: list[float] = []
        indices: list[int] = []

        # Side
        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            # Approx cone side normal
            nx = cos_a
            ny = radius / height
            nz = sin_a
            length = math.sqrt(nx * nx + ny * ny + nz * nz)

            vertices.extend([
                x, -half_height, z,
                nx / length, ny / length, nz / length,
                u, 0.0,
            ])

            vertices.extend([
                0.0, half_height, 0.0,
                nx / length, ny / length, nz / length,
                u, 1.0,
            ])

        for i in range(segments):
            base = i * 2

            indices.extend([
                base,
                base + 2,
                base + 1,
            ])

        # Bottom cap
        center_index = len(vertices) // 8

        vertices.extend([
            0.0, -half_height, 0.0,
            0.0, -1.0, 0.0,
            0.5, 0.5,
        ])

        start = center_index + 1

        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            vertices.extend([
                cos_a * radius, -half_height, sin_a * radius,
                0.0, -1.0, 0.0,
                cos_a * 0.5 + 0.5, sin_a * 0.5 + 0.5,
            ])

        for i in range(segments):
            indices.extend([
                center_index,
                start + i + 1,
                start + i,
            ])

        mesh_data = MeshData(
            vertices=vertices,
            indices=indices,
        )

        super().__init__(
            mesh_data=mesh_data,
            material=material or Material(),
            **kwargs,
        )
