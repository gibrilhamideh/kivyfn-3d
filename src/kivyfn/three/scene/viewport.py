# kivyfn/three/scene/viewport.py

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from kivy.graphics.transformation import Matrix

from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.scene.view import View


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

        camera_x = ndc_x * right
        camera_y = ndc_y * top
        camera_z = -view.near

        inverse_view = view.get_view_matrix().inverse()

        origin = self._transform_point(
            inverse_view,
            0.0,
            0.0,
            0.0,
        )

        target = self._transform_point(
            inverse_view,
            camera_x,
            camera_y,
            camera_z,
        )

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

        camera_x = ndc_x * right
        camera_y = ndc_y * top

        inverse_view = view.get_view_matrix().inverse()

        origin = self._transform_point(
            inverse_view,
            camera_x,
            camera_y,
            0.0,
        )

        target = self._transform_point(
            inverse_view,
            camera_x,
            camera_y,
            -1.0,
        )

        direction = (target - origin).normalize()

        return origin, direction

    def _transform_point(
        self,
        matrix: Matrix,
        x: float,
        y: float,
        z: float,
    ) -> Vector3:
        result = matrix.transform_point(x, y, z)

        return Vector3(
            result[0],
            result[1],
            result[2],
        )
