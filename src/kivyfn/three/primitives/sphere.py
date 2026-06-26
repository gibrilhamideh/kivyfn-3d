# kivyfn/three/primitives/sphere.py

from __future__ import annotations

import math

import numpy as np

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D


class Sphere(Object3D):
    def __init__(
        self,
        radius: float = 0.5,
        segments: int = 32,
        rings: int = 16,
        material: Material | None = None,
        with_tangents: bool = True,
        **kwargs,
    ):
        if radius <= 0.0:
            raise ValueError(
                "Sphere radius must be greater than 0."
            )

        if segments < 3:
            raise ValueError(
                "Sphere segments must be at least 3."
            )

        if rings < 2:
            raise ValueError(
                "Sphere rings must be at least 2."
            )

        vertices_with_tangents: list[float] = []
        indices: list[int] = []

        # =================================== #
        # Vertices
        # =================================== #

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

                tangent_x = -sin_phi
                tangent_y = 0.0
                tangent_z = cos_phi

                vertices_with_tangents.extend(
                    [
                        px, py, pz,
                        nx, ny, nz,
                        u, 1.0 - v,
                        tangent_x, tangent_y, tangent_z, 1.0,
                    ]
                )

        # =================================== #
        # Indices
        # =================================== #

        stride = segments + 1

        for ring in range(rings):
            for segment in range(segments):
                current = ring * stride + segment
                next_row = current + stride

                indices.extend(
                    [
                        current,
                        next_row,
                        current + 1,

                        current + 1,
                        next_row,
                        next_row + 1,
                    ]
                )

        vertices_array = np.array(
            vertices_with_tangents,
            dtype=np.float32,
        )

        if with_tangents:
            vertices = vertices_array

            fmt = [
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
                (b"v_tangent", 4, "float"),
            ]

        else:
            vertices = vertices_array.reshape(
                -1,
                12,
            )[:, :8].reshape(-1)

            fmt = [
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
            ]

        geometry = Geometry(
            fmt=fmt,
            vertices=vertices,
            indices=np.array(
                indices,
                dtype=np.uint16,
            ),
            has_tangents=with_tangents,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )
