
from __future__ import annotations

import math

from kivyfn.three.math.vector import Vector3
from kivyfn.three.views.view import View
from kivyfn.three.views.rect import ViewRect



class ViewTransform:
    # =================================== #
    # Screen -> NDC
    # =================================== #

    @classmethod
    def screen_to_ndc(
        cls,
        rect: ViewRect,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        if rect.width <= 0 or rect.height <= 0:
            raise RuntimeError(
                "Cannot convert screen coordinates to NDC because "
                f"view rect size is invalid: {rect.width}x{rect.height}."
            )

        local_x = x - rect.x
        local_y = y - rect.y

        ndc_x = (2.0 * local_x / rect.width) - 1.0
        ndc_y = (2.0 * local_y / rect.height) - 1.0

        return ndc_x, ndc_y

    # =================================== #
    # World -> Screen
    # =================================== #

    @classmethod
    def world_to_screen(
        cls,
        rect: ViewRect,
        view: View,
        point: Vector3,
    ) -> tuple[float, float, float] | None:
        projection = view.get_projection_matrix(mode="planar", aspect=rect.aspect)
        view_matrix = view.get_view_matrix()

        ndc = (projection @ view_matrix).transform_point(point)

        if ndc.z < -1.0 or ndc.z > 1.0:
            return None

        x = rect.x + ((ndc.x + 1.0) * 0.5 * rect.width)
        y = rect.y + ((ndc.y + 1.0) * 0.5 * rect.height)

        return x, y, ndc.z

    # =================================== #
    # Screen -> Ray
    # =================================== #

    @classmethod
    def screen_to_ray(
        cls,
        rect: ViewRect,
        view: View,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        if view.projection == "orthographic":
            return cls._screen_to_orthographic_ray(
                rect,
                view,
                x,
                y,
            )

        return cls._screen_to_perspective_ray(
            rect,
            view,
            x,
            y,
        )

    @classmethod
    def _screen_to_perspective_ray(
        cls,
        rect: ViewRect,
        view: View,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        ndc_x, ndc_y = cls.screen_to_ndc(
            rect,
            x,
            y,
        )

        top = view.near * math.tan(
            math.radians(view.fov) / 2.0
        )
        right = top * rect.aspect

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

    @classmethod
    def _screen_to_orthographic_ray(
        cls,
        rect: ViewRect,
        view: View,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        ndc_x, ndc_y = cls.screen_to_ndc(
            rect,
            x,
            y,
        )

        right = view.ortho_size / 2.0
        top = right / rect.aspect

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
