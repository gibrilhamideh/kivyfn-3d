# kivyfn/three/collision/collider.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

from kivyfn.three.collision.intersections import (
    sphere_intersect,
    triangle_intersect,
)
from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D


class Collider(EventDispatcher):
    def __init__(
        self,
        object3d: Object3D,
    ) -> None:
        super().__init__()

        self.object3d = object3d

    @property
    def geometry(self):
        return self.object3d.geometry

    @property
    def world_matrix(self):
        return self.object3d.world_matrix

    def iter_triangles(self):
        positions = self.geometry.get_positions()
        indices = self.geometry.indices

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
        bounds = self.geometry.bounds

        if bounds.radius <= 0.0:
            return False

        return sphere_intersect(
            ray_origin,
            ray_direction,
            tuple(bounds.center),
            bounds.radius,
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

        world_point_raw = self.world_matrix.transform_point(point)

        world_point = Vector3(*world_point_raw)
        world_distance = (world_point - ray_origin).length

        return world_distance, world_point

    def _local_ray(
        self,
        ray_origin,
        ray_direction,
    ):
        inverse = self.world_matrix.inverse()

        local_origin_raw = inverse.transform_point(ray_origin)

        world_target = ray_origin + ray_direction

        local_target_raw = inverse.transform_point(world_target)

        local_origin = Vector3(*local_origin_raw)
        local_target = Vector3(*local_target_raw)

        local_direction = (
            local_target - local_origin
        ).normalize()

        return local_origin, local_direction
