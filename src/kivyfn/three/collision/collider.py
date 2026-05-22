# kivyfn/collision/collider.py
from __future__ import annotations
from typing import TYPE_CHECKING, Iterator

from kivy.event import EventDispatcher
from kivyfn.three.math.vector import Vector3
from kivyfn.three.collision.intersections import sphere_intersect, triangle_intersect

import math

if TYPE_CHECKING:
    from kivyfn.three.objects import Object3D


class Collider(EventDispatcher):

    def __init__(self, object3d: Object3D) -> None:
        self.object3d = object3d
        self.object3d.bind(pivot=self.on_pivot)

    @property
    def geometry(self):
        return self.object3d.geometry

    @property
    def pivot(self):
        return self.object3d.pivot

    @property
    def world_matrix(self):
        return self.object3d.world_matrix

    def on_pivot(self, *_):
        self.compute_bounds()


    def compute_bounds(self) -> None:
        vertices = self.geometry.vertices

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

        if self.pivot == "center":
            origin = Vector3(center_x, center_y, center_z)
        elif self.pivot == "bottom":
            origin = Vector3(center_x, y_min, center_z)
        elif self.pivot == "top":
            origin = Vector3(center_x, y_max, center_z)
        elif self.pivot == "left":
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
        vertices = self.geometry.vertices
        indices = self.geometry.indices

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

    def intersects_ray(self, ray_origin, ray_direction):
        local_origin, local_direction = self._local_ray(
            ray_origin,
            ray_direction,
        )

        if not self.intersects_bounds(local_origin, local_direction):
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


    def _local_ray(self, ray_origin, ray_direction):
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

        local_direction = (local_target - local_origin).normalize()

        return local_origin, local_direction
