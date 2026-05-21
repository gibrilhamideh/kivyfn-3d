# kivyfn/three/primitive/sphere.py

from __future__ import annotations

import math

from kivyfn.three.render.material import Material
from kivyfn.three.render.meshdata import MeshData
from kivyfn.three.scene.object3d import Object3D


class Sphere(Object3D):
    def __init__(
        self,
        radius: float = 0.5,
        segments: int = 32,
        rings: int = 16,
        material: Material | None = None,
        **kwargs,
    ):
        vertices: list[float] = []
        indices: list[int] = []

        # ==========================================
        # Vertices
        # ==========================================
        for ring in range(rings + 1):
            v = ring / rings
            theta = v * math.pi

            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            for segment in range(segments + 1):
                u = segment / segments
                phi = u * math.pi * 2.0

                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                x = cos_phi * sin_theta
                y = cos_theta
                z = sin_phi * sin_theta

                px = x * radius
                py = y * radius
                pz = z * radius

                nx = x
                ny = y
                nz = z

                vertices.extend([
                    px, py, pz,
                    nx, ny, nz,
                    u, 1.0 - v,
                ])

        # ==========================================
        # Indices
        # ==========================================
        stride = segments + 1

        for ring in range(rings):
            for segment in range(segments):
                current = ring * stride + segment
                next_row = current + stride

                indices.extend([
                    current,
                    next_row,
                    current + 1,

                    current + 1,
                    next_row,
                    next_row + 1,
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
