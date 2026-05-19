# kivyfn/three/scene/meshnode.py

from __future__ import annotations

import math
from typing import Iterator

from kivy.properties import NumericProperty, ObjectProperty, OptionProperty

from kivyfn.three.collision.intersections import sphere_intersect, triangle_intersect
from kivyfn.three.math.vector import Vector3
from kivyfn.three.render.meshdata import MeshData
from kivyfn.three.scene.node import Node3D


class MeshNode(Node3D):
    mesh_data = ObjectProperty(None, allownone=True)

    origin_mode = OptionProperty(
        "center",
        options=("center", "bottom", "top", "left", "right"),
    )

    origin = ObjectProperty(None, allownone=True)
    radius = NumericProperty(0.0)

    bounds_min = ObjectProperty(None, allownone=True)
    bounds_max = ObjectProperty(None, allownone=True)

    def __init__(
        self,
        name: str = "",
        mesh_data: MeshData | None = None,
        origin_mode: str = "center",
        **kwargs,
    ):
        super().__init__(
            name=name,
            **kwargs,
        )

        self.origin_mode = origin_mode
        self.mesh_data = mesh_data

        self.origin = Vector3.zero()
        self.bounds_min = Vector3.zero()
        self.bounds_max = Vector3.zero()

        if self.mesh_data is not None:
            self.recalculate_bounds()

    def on_mesh_data(
        self,
        instance,
        value: MeshData | None,
    ) -> None:
        if value is not None:
            self.recalculate_bounds()

    def on_origin_mode(
        self,
        instance,
        value: str,
    ) -> None:
        if self.mesh_data is not None:
            self.recalculate_bounds()

    def recalculate_bounds(self) -> None:
        if self.mesh_data is None or not self.mesh_data.vertices:
            self.origin = Vector3.zero()
            self.bounds_min = Vector3.zero()
            self.bounds_max = Vector3.zero()
            self.radius = 0.0
            return

        vertices = self.mesh_data.vertices

        xs = vertices[0::8]
        ys = vertices[1::8]
        zs = vertices[2::8]

        x_min = min(xs)
        y_min = min(ys)
        z_min = min(zs)

        x_max = max(xs)
        y_max = max(ys)
        z_max = max(zs)

        self.bounds_min = Vector3(x_min, y_min, z_min)
        self.bounds_max = Vector3(x_max, y_max, z_max)

        center_x = (x_min + x_max) / 2.0
        center_y = (y_min + y_max) / 2.0
        center_z = (z_min + z_max) / 2.0

        if self.origin_mode == "center":
            origin = Vector3(center_x, center_y, center_z)
        elif self.origin_mode == "bottom":
            origin = Vector3(center_x, y_min, center_z)
        elif self.origin_mode == "top":
            origin = Vector3(center_x, y_max, center_z)
        elif self.origin_mode == "left":
            origin = Vector3(x_min, center_y, center_z)
        else:
            origin = Vector3(x_max, center_y, center_z)

        self.origin = origin

        self.radius = max(
            math.dist(
                (vertices[index], vertices[index + 1], vertices[index + 2]),
                tuple(origin),
            )
            for index in range(0, len(vertices), 8)
        )

    def iter_triangles(
        self,
    ) -> Iterator[tuple[Vector3, Vector3, Vector3]]:
        if self.mesh_data is None:
            return

        vertices = self.mesh_data.vertices
        indices = self.mesh_data.indices

        for index in range(0, len(indices), 3):
            i0, i1, i2 = indices[index:index + 3]

            yield (
                Vector3(*vertices[i0 * 8:i0 * 8 + 3]),
                Vector3(*vertices[i1 * 8:i1 * 8 + 3]),
                Vector3(*vertices[i2 * 8:i2 * 8 + 3]),
            )

    def intersects_bounds(
        self,
        ray_origin,
        ray_direction,
    ) -> bool:
        if self.radius <= 0.0:
            return False

        return sphere_intersect(
            ray_origin,
            ray_direction,
            tuple(self.origin),
            self.radius,
        )

    def intersects_geometry(
        self,
        ray_origin,
        ray_direction,
    ):
        closest = None

        ray_origin_tuple = tuple(ray_origin)
        ray_direction_tuple = tuple(ray_direction)

        for v0, v1, v2 in self.iter_triangles():
            distance, point = triangle_intersect(
                ray_origin_tuple,
                ray_direction_tuple,
                tuple(v0),
                tuple(v1),
                tuple(v2),
            )

            if distance is not None and point is not None:
                if closest is None or distance < closest[0]:
                    closest = (
                        distance,
                        Vector3(*point),
                    )

        return closest or (None, None)

    def intersects_ray(
        self,
        ray_origin,
        ray_direction,
    ):
        if not self.intersects_bounds(ray_origin, ray_direction):
            return None

        distance, point = self.intersects_geometry(
            ray_origin,
            ray_direction,
        )

        if distance is None:
            return None

        return distance, point


    def __repr__(self) -> str:
        return (
            f"MeshNode("
            f"name={self.name!r}, "
            f"mesh_data={self.mesh_data is not None}, "
            f"children={len(self.children)})"
        )
