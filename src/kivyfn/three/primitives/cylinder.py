# kivyfn/three/primitives/cylinder.py

from __future__ import annotations

import math

import numpy as np

from kivyfn.three.objects.material import Material
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.objects.geometry import Geometry


class Cylinder(Object3D):
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

        # ==========================================
        # Side vertices
        # ==========================================
        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            nx = cos_a
            ny = 0.0
            nz = sin_a

            tangent_x = -sin_a
            tangent_y = 0.0
            tangent_z = cos_a

            # Bottom
            vertices.extend([
                x, -half_height, z,
                nx, ny, nz,
                u, 0.0,
                tangent_x, tangent_y, tangent_z, 1.0,
            ])

            # Top
            vertices.extend([
                x, half_height, z,
                nx, ny, nz,
                u, 1.0,
                tangent_x, tangent_y, tangent_z, 1.0,
            ])

        # ==========================================
        # Side indices
        # ==========================================
        for i in range(segments):
            base = i * 2

            indices.extend([
                base,
                base + 1,
                base + 2,

                base + 2,
                base + 1,
                base + 3,
            ])

        # ==========================================
        # Top center vertex
        # ==========================================
        top_center_index = len(vertices) // 12

        vertices.extend([
            0.0, half_height, 0.0,
            0.0, 1.0, 0.0,
            0.5, 0.5,
            1.0, 0.0, 0.0, 1.0,
        ])

        # Top ring
        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            vertices.extend([
                x, half_height, z,
                0.0, 1.0, 0.0,
                (cos_a * 0.5) + 0.5,
                (sin_a * 0.5) + 0.5,
                1.0, 0.0, 0.0, 1.0,
            ])

        top_start = top_center_index + 1

        for i in range(segments):
            indices.extend([
                top_center_index,
                top_start + i,
                top_start + i + 1,
            ])

        # ==========================================
        # Bottom center vertex
        # ==========================================
        bottom_center_index = len(vertices) // 12

        vertices.extend([
            0.0, -half_height, 0.0,
            0.0, -1.0, 0.0,
            0.5, 0.5,
            1.0, 0.0, 0.0, 1.0,
        ])

        # Bottom ring
        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            vertices.extend([
                x, -half_height, z,
                0.0, -1.0, 0.0,
                (cos_a * 0.5) + 0.5,
                (sin_a * 0.5) + 0.5,
                1.0, 0.0, 0.0, 1.0,
            ])

        bottom_start = bottom_center_index + 1

        for i in range(segments):
            indices.extend([
                bottom_center_index,
                bottom_start + i + 1,
                bottom_start + i,
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
