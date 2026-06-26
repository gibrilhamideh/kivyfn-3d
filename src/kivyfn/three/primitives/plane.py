# kivyfn/three/primitives/plane.py

from __future__ import annotations

import math

import numpy as np

from kivy.properties import OptionProperty

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D


class Plane(Object3D):
    axis = OptionProperty(
        "xz",
        options=("xy", "xz", "yz"),
    )

    shape = OptionProperty(
        "rectangle",
        options=("rectangle", "circle"),
    )

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.0,
        axis: str = "xz",
        shape: str = "rectangle",
        segments: int = 64,
        material: Material | None = None,
        with_tangents: bool = True,
        **kwargs,
    ):
        if width <= 0.0:
            raise ValueError(
                "Plane width must be greater than 0."
            )

        if height <= 0.0:
            raise ValueError(
                "Plane height must be greater than 0."
            )

        self.axis = axis
        self.shape = shape

        geometry = self._create_geometry(
            width=width,
            height=height,
            axis=axis,
            shape=shape,
            segments=segments,
            with_tangents=with_tangents,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )

    def _create_geometry(
        self,
        width: float,
        height: float,
        axis: str,
        shape: str,
        segments: int,
        with_tangents: bool,
    ) -> Geometry:
        if shape == "rectangle":
            return self._create_rectangle_geometry(
                width=width,
                height=height,
                axis=axis,
                with_tangents=with_tangents,
            )

        if shape == "circle":
            return self._create_circle_geometry(
                width=width,
                height=height,
                axis=axis,
                segments=segments,
                with_tangents=with_tangents,
            )

        raise ValueError(
            f"Invalid plane shape {shape!r}. "
            "Expected 'rectangle' or 'circle'."
        )

    def _create_rectangle_geometry(
        self,
        width: float,
        height: float,
        axis: str,
        with_tangents: bool,
    ) -> Geometry:
        hw = width / 2.0
        hh = height / 2.0

        if axis == "xy":
            vertices_with_tangents = [
                -hw, -hh, 0.0,  0, 0, 1,  0, 0,  1, 0, 0, 1,
                 hw, -hh, 0.0,  0, 0, 1,  1, 0,  1, 0, 0, 1,
                 hw,  hh, 0.0,  0, 0, 1,  1, 1,  1, 0, 0, 1,
                -hw,  hh, 0.0,  0, 0, 1,  0, 1,  1, 0, 0, 1,
            ]

        elif axis == "xz":
            vertices_with_tangents = [
                -hw, 0.0, -hh,  0, 1, 0,  0, 0,  1, 0, 0, 1,
                 hw, 0.0, -hh,  0, 1, 0,  1, 0,  1, 0, 0, 1,
                 hw, 0.0,  hh,  0, 1, 0,  1, 1,  1, 0, 0, 1,
                -hw, 0.0,  hh,  0, 1, 0,  0, 1,  1, 0, 0, 1,
            ]

        elif axis == "yz":
            vertices_with_tangents = [
                0.0, -hw, -hh,  1, 0, 0,  0, 0,  0, 1, 0, 1,
                0.0,  hw, -hh,  1, 0, 0,  1, 0,  0, 1, 0, 1,
                0.0,  hw,  hh,  1, 0, 0,  1, 1,  0, 1, 0, 1,
                0.0, -hw,  hh,  1, 0, 0,  0, 1,  0, 1, 0, 1,
            ]

        else:
            raise ValueError(
                f"Invalid plane axis {axis!r}. "
                "Expected 'xy', 'xz', or 'yz'."
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

        indices = np.array(
            [
                0, 1, 2,
                2, 3, 0,
            ],
            dtype=np.uint16,
        )

        return Geometry(
            fmt=fmt,
            vertices=vertices,
            indices=indices,
            has_tangents=with_tangents,
        )

    def _create_circle_geometry(
        self,
        width: float,
        height: float,
        axis: str,
        segments: int,
        with_tangents: bool,
    ) -> Geometry:
        if segments < 3:
            raise ValueError(
                "Circle plane requires at least 3 segments."
            )

        rx = width / 2.0
        rz = height / 2.0

        vertices_with_tangents: list[float] = []
        indices: list[int] = []

        center_pos = self._make_position(
            axis=axis,
            x=0.0,
            y=0.0,
        )

        normal = self._make_normal(axis)
        tangent = self._make_tangent(axis)

        vertices_with_tangents.extend(
            [
                *center_pos,
                *normal,
                0.5,
                0.5,
                *tangent,
            ]
        )

        for index in range(segments):
            angle = 2.0 * math.pi * index / segments

            x = math.cos(angle) * rx
            y = math.sin(angle) * rz

            u = 0.5 + math.cos(angle) * 0.5
            v = 0.5 + math.sin(angle) * 0.5

            position = self._make_position(
                axis=axis,
                x=x,
                y=y,
            )

            vertices_with_tangents.extend(
                [
                    *position,
                    *normal,
                    u,
                    v,
                    *tangent,
                ]
            )

        for index in range(segments):
            current_vertex = index + 1
            next_vertex = ((index + 1) % segments) + 1

            indices.extend(
                [
                    0,
                    current_vertex,
                    next_vertex,
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

        return Geometry(
            fmt=fmt,
            vertices=vertices,
            indices=np.array(
                indices,
                dtype=np.uint16,
            ),
            has_tangents=with_tangents,
        )

    def _make_position(
        self,
        *,
        axis: str,
        x: float,
        y: float,
    ) -> tuple[float, float, float]:
        if axis == "xy":
            return (
                x,
                y,
                0.0,
            )

        if axis == "xz":
            return (
                x,
                0.0,
                y,
            )

        if axis == "yz":
            return (
                0.0,
                x,
                y,
            )

        raise ValueError(
            f"Invalid plane axis {axis!r}. "
            "Expected 'xy', 'xz', or 'yz'."
        )

    def _make_normal(
        self,
        axis: str,
    ) -> tuple[float, float, float]:
        if axis == "xy":
            return (
                0.0,
                0.0,
                1.0,
            )

        if axis == "xz":
            return (
                0.0,
                1.0,
                0.0,
            )

        if axis == "yz":
            return (
                1.0,
                0.0,
                0.0,
            )

        raise ValueError(
            f"Invalid plane axis {axis!r}. "
            "Expected 'xy', 'xz', or 'yz'."
        )

    def _make_tangent(
        self,
        axis: str,
    ) -> tuple[float, float, float, float]:
        if axis == "xy":
            return (
                1.0,
                0.0,
                0.0,
                1.0,
            )

        if axis == "xz":
            return (
                1.0,
                0.0,
                0.0,
                1.0,
            )

        if axis == "yz":
            return (
                0.0,
                1.0,
                0.0,
                1.0,
            )

        raise ValueError(
            f"Invalid plane axis {axis!r}. "
            "Expected 'xy', 'xz', or 'yz'."
        )
