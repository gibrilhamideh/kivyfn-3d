# kivyfn/three/scene/viewport.py

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.view import View


class Viewport:
    def __init__(self, scene: Scene):
        self.scene = scene

    @property
    def width(self) -> float:
        return max(self.scene.width, 1.0)

    @property
    def height(self) -> float:
        return max(self.scene.height, 1.0)

    @property
    def aspect(self) -> float:
        return self.width / self.height

    def world_to_screen(
        self,
        point: Vector3,
        *,
        view: View,
    ) -> tuple[float, float, float] | None:
        projection = view.get_projection_matrix(self.aspect)
        view_matrix = view.get_view_matrix()

        ndc = (projection @ view_matrix).transform_point(point)

        if ndc.z < -1.0 or ndc.z > 1.0:
            return None

        x = self.scene.x + ((ndc.x + 1.0) * 0.5 * self.width)
        y = self.scene.y + ((ndc.y + 1.0) * 0.5 * self.height)

        return x, y, ndc.z

    def screen_to_ndc(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        local_x, local_y = self.scene.to_widget(x, y)

        ndc_x = (2.0 * local_x / self.width) - 1.0
        ndc_y = (2.0 * local_y / self.height) - 1.0

        return ndc_x, ndc_y

    def screen_to_ray(
        self,
        x: float,
        y: float,
        *,
        view: View,
    ) -> tuple[Vector3, Vector3]:
        if view.projection_type == "orthographic":
            return self._screen_to_orthographic_ray(
                x,
                y,
                view=view,
            )

        return self._screen_to_perspective_ray(
            x,
            y,
            view=view,
        )

    def _screen_to_perspective_ray(
        self,
        x: float,
        y: float,
        *,
        view: View,
    ) -> tuple[Vector3, Vector3]:
        ndc_x, ndc_y = self.screen_to_ndc(x, y)

        top = view.near * math.tan(
            math.radians(view.fov) / 2.0
        )
        right = top * self.aspect

        camera_point = Vector3(
            ndc_x * right,
            ndc_y * top,
            -view.near,
        )

        inverse_view = view.get_view_matrix().inverse()

        origin = inverse_view.transform_point(Vector3.zero())
        target = inverse_view.transform_point(camera_point)

        direction = (target - origin).normalize()

        return origin, direction

    def _screen_to_orthographic_ray(
        self,
        x: float,
        y: float,
        *,
        view: View,
    ) -> tuple[Vector3, Vector3]:
        ndc_x, ndc_y = self.screen_to_ndc(x, y)

        right = view.ortho_size / 2.0
        top = right / self.aspect

        origin_camera = Vector3(
            ndc_x * right,
            ndc_y * top,
            0.0,
        )

        target_camera = Vector3(
            ndc_x * right,
            ndc_y * top,
            -1.0,
        )

        inverse_view = view.get_view_matrix().inverse()

        origin = inverse_view.transform_point(origin_camera)
        target = inverse_view.transform_point(target_camera)

        direction = (target - origin).normalize()

        return origin, direction


