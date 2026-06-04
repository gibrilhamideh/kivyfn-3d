# kivyfn/three/primitives/cone.py

from __future__ import annotations

import math

import numpy as np

from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.assets.geometry import Geometry


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

            nx = cos_a
            ny = radius / height
            nz = sin_a
            length = math.sqrt(nx * nx + ny * ny + nz * nz)

            tangent_x = -sin_a
            tangent_y = 0.0
            tangent_z = cos_a

            vertices.extend([
                x, -half_height, z,
                nx / length, ny / length, nz / length,
                u, 0.0,
                tangent_x, tangent_y, tangent_z, 1.0,
            ])

            vertices.extend([
                0.0, half_height, 0.0,
                nx / length, ny / length, nz / length,
                u, 1.0,
                tangent_x, tangent_y, tangent_z, 1.0,
            ])

        for i in range(segments):
            base = i * 2

            indices.extend([
                base,
                base + 2,
                base + 1,
            ])

        # Bottom cap
        center_index = len(vertices) // 12

        vertices.extend([
            0.0, -half_height, 0.0,
            0.0, -1.0, 0.0,
            0.5, 0.5,
            1.0, 0.0, 0.0, 1.0,
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
                1.0, 0.0, 0.0, 1.0,
            ])

        for i in range(segments):
            indices.extend([
                center_index,
                start + i + 1,
                start + i,
            ])

        geometry = Geometry(
            vertices=np.array(
                vertices,
                dtype=np.float32,
            ),
            indices=np.array(
                indices,
                dtype=np.uint16,
            ),
            has_source_tangents=False,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )
