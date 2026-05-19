# kivyfn/three/scene/viewport.py

from __future__ import annotations

import math

from kivyfn.three.math.vector import Vector3


class Viewport:
    def __init__(self, scene):
        self.scene = scene

    @property
    def aspect(self) -> float:
        return self.width / self.height

    @property
    def width(self) -> float:
        return max(self.scene.width, 1.0)

    @property
    def height(self) -> float:
        return max(self.scene.height, 1.0)

    def screen_to_ndc(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        ndc_x = (2.0 * (x - self.scene.x) / self.width) - 1.0
        ndc_y = (2.0 * (y - self.scene.y) / self.height) - 1.0
        return ndc_x, ndc_y

    def screen_to_camera_space(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float, float]:
        ndc_x, ndc_y = self.screen_to_ndc(x, y)

        near = self.scene.camera.near
        fov = math.radians(self.scene.camera.fov)

        top = near * math.tan(fov / 2.0)
        right = top * self.aspect

        camera_x = ndc_x * right
        camera_y = ndc_y * top
        camera_z = -near

        return camera_x, camera_y, camera_z

    def screen_to_ray(
        self,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        camera_x, camera_y, camera_z = self.screen_to_camera_space(x, y)

        inverse_modelview = self.scene.modelview_mat.inverse()

        origin = inverse_modelview.transform_point(0.0, 0.0, 0.0)
        target = inverse_modelview.transform_point(
            camera_x,
            camera_y,
            camera_z,
        )

        origin_v = Vector3(*origin)
        target_v = Vector3(*target)

        direction = (target_v - origin_v).normalize()

        return origin_v, direction
