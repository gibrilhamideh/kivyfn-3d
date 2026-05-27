# kivyfn/three/collision/collider.py

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

import numpy as np
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ObjectProperty, OptionProperty

from kivyfn.three.collision.intersections import sphere_intersect, triangle_intersect
from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.objects import Object3D


Pivot = Literal[
    "center",
    "bottom",
    "top",
    "left",
    "right",
]


class Collider(EventDispatcher):

    radius: float = NumericProperty(0.0)
    origin: Vector3 = ObjectProperty()
    bounds_min: Vector3 = ObjectProperty(Vector3.zero())
    bounds_max: Vector3 = ObjectProperty(Vector3.zero())

    pivot: Pivot = OptionProperty(
        "center",
        options=(
            "center",
            "bottom",
            "top",
            "left",
            "right",
        ),
    )

    def __init__(self, object3d: Object3D) -> None:
        super().__init__()

        self.object3d = object3d

    @property
    def geometry(self):
        return self.object3d.geometry

    @property
    def world_matrix(self):
        return self.object3d.world_matrix

    def on_pivot(self, *_):
        self.compute_bounds()

    def compute_bounds(self) -> None:
        vertices = self.geometry.vertices
        stride = self.geometry.stride

        if vertices.size == 0:
            self.bounds_min = Vector3.zero()
            self.bounds_max = Vector3.zero()
            self.origin = Vector3.zero()
            self.radius = 0.0
            return

        vertex_data = vertices.reshape(
            -1,
            stride,
        )

        positions = vertex_data[:, :3]

        mins = positions.min(axis=0)
        maxs = positions.max(axis=0)

        x_min, y_min, z_min = mins
        x_max, y_max, z_max = maxs

        self.bounds_min = Vector3(
            float(x_min),
            float(y_min),
            float(z_min),
        )

        self.bounds_max = Vector3(
            float(x_max),
            float(y_max),
            float(z_max),
        )

        center = (mins + maxs) * 0.5

        center_x, center_y, center_z = center

        if self.pivot == "center":
            origin_values = center

        elif self.pivot == "bottom":
            origin_values = np.array(
                [center_x, y_min, center_z],
                dtype=np.float32,
            )

        elif self.pivot == "top":
            origin_values = np.array(
                [center_x, y_max, center_z],
                dtype=np.float32,
            )

        elif self.pivot == "left":
            origin_values = np.array(
                [x_min, center_y, center_z],
                dtype=np.float32,
            )

        else:
            origin_values = np.array(
                [x_max, center_y, center_z],
                dtype=np.float32,
            )

        self.origin = Vector3(
            float(origin_values[0]),
            float(origin_values[1]),
            float(origin_values[2]),
        )

        distances = np.linalg.norm(
            positions - origin_values,
            axis=1,
        )

        self.radius = float(distances.max())

    def iter_triangles(self):
        vertices = self.geometry.vertices
        indices = self.geometry.indices
        stride = self.geometry.stride

        vertex_data = vertices.reshape(
            -1,
            stride,
        )

        positions = vertex_data[:, :3]

        for index in range(0, len(indices), 3):
            i0, i1, i2 = indices[index:index + 3]

            yield (
                Vector3(*positions[int(i0)]),
                Vector3(*positions[int(i1)]),
                Vector3(*positions[int(i2)]),
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
        local_origin, local_direction = self._local_ray(
            ray_origin,
            ray_direction,
        )

        if not self.intersects_bounds(
            local_origin,
            local_direction,
        ):
            return None

        distance, point = self.intersects_geometry(
            local_origin,
            local_direction,
        )

        if distance is None or point is None:
            return None

        world_point_raw = self.world_matrix.transform_point(
            point.x,
            point.y,
            point.z,
        )

        world_point = Vector3(*world_point_raw)

        world_distance = (world_point - ray_origin).length

        return world_distance, world_point

    def _local_ray(
        self,
        ray_origin,
        ray_direction,
    ):
        inverse = self.world_matrix.inverse()

        local_origin = inverse.transform_point(
            ray_origin.x,
            ray_origin.y,
            ray_origin.z,
        )

        world_target = ray_origin + ray_direction

        local_target = inverse.transform_point(
            world_target.x,
            world_target.y,
            world_target.z,
        )

        local_origin = Vector3(*local_origin)
        local_target = Vector3(*local_target)

        local_direction = (
            local_target - local_origin
        ).normalize()

        return local_origin, local_direction
