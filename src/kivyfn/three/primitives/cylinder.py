# kivyfn/three/primitives/cylinder.py

from __future__ import annotations

import math

import numpy as np

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D


class Cylinder(Object3D):
    def __init__(
        self,
        radius: float = 0.5,
        height: float = 1.0,
        segments: int = 32,
        material: Material | None = None,
        with_tangents: bool = True,
        **kwargs,
    ):
        if radius <= 0.0:
            raise ValueError(
                "Cylinder radius must be greater than 0."
            )

        if height <= 0.0:
            raise ValueError(
                "Cylinder height must be greater than 0."
            )

        if segments < 3:
            raise ValueError(
                "Cylinder segments must be at least 3."
            )

        half_height = height / 2.0

        vertices_with_tangents: list[float] = []
        indices: list[int] = []

        # =================================== #
        # Side vertices
        # =================================== #

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

            vertices_with_tangents.extend(
                [
                    x, -half_height, z,
                    nx, ny, nz,
                    u, 0.0,
                    tangent_x, tangent_y, tangent_z, 1.0,
                ]
            )

            vertices_with_tangents.extend(
                [
                    x, half_height, z,
                    nx, ny, nz,
                    u, 1.0,
                    tangent_x, tangent_y, tangent_z, 1.0,
                ]
            )

        # =================================== #
        # Side indices
        # =================================== #

        for i in range(segments):
            base = i * 2

            indices.extend(
                [
                    base,
                    base + 1,
                    base + 2,

                    base + 2,
                    base + 1,
                    base + 3,
                ]
            )

        # =================================== #
        # Top cap
        # =================================== #

        top_center_index = len(vertices_with_tangents) // 12

        vertices_with_tangents.extend(
            [
                0.0, half_height, 0.0,
                0.0, 1.0, 0.0,
                0.5, 0.5,
                1.0, 0.0, 0.0, 1.0,
            ]
        )

        top_start = top_center_index + 1

        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            vertices_with_tangents.extend(
                [
                    x, half_height, z,
                    0.0, 1.0, 0.0,
                    cos_a * 0.5 + 0.5,
                    sin_a * 0.5 + 0.5,
                    1.0, 0.0, 0.0, 1.0,
                ]
            )

        for i in range(segments):
            indices.extend(
                [
                    top_center_index,
                    top_start + i,
                    top_start + i + 1,
                ]
            )

        # =================================== #
        # Bottom cap
        # =================================== #

        bottom_center_index = len(vertices_with_tangents) // 12

        vertices_with_tangents.extend(
            [
                0.0, -half_height, 0.0,
                0.0, -1.0, 0.0,
                0.5, 0.5,
                1.0, 0.0, 0.0, 1.0,
            ]
        )

        bottom_start = bottom_center_index + 1

        for i in range(segments + 1):
            u = i / segments
            angle = u * math.pi * 2.0

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            x = cos_a * radius
            z = sin_a * radius

            vertices_with_tangents.extend(
                [
                    x, -half_height, z,
                    0.0, -1.0, 0.0,
                    cos_a * 0.5 + 0.5,
                    sin_a * 0.5 + 0.5,
                    1.0, 0.0, 0.0, 1.0,
                ]
            )

        for i in range(segments):
            indices.extend(
                [
                    bottom_center_index,
                    bottom_start + i + 1,
                    bottom_start + i,
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
