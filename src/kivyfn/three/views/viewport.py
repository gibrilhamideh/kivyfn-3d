# kivyfn/three/views/viewport.py

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

from kivy.graphics.opengl import glViewport
from kivy.event import EventDispatcher
from kivy.properties import (
        NumericProperty,
        OptionProperty,
        AliasProperty,
)

from kivyfn.three.math.vector import Vector3
from kivyfn.three.views.view import View

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene


class Viewport(EventDispatcher):

    viewport_mode: Literal["scene", "local"] = OptionProperty(
        "scene", options=["scene", "local"]
    )

    scene_x: int = NumericProperty()
    scene_y: int = NumericProperty()
    scene_width: int = NumericProperty()
    scene_height: int = NumericProperty()

    local_x: int = NumericProperty()
    local_y: int = NumericProperty()
    local_width: int = NumericProperty()
    local_height: int = NumericProperty()


    def _get_x(self) -> int:
        if self.viewport_mode == "scene":
            return self.scene_x

        return self.local_x

    def _get_y(self) -> int:
        if self.viewport_mode == "scene":
            return self.scene_y

        return self.local_y

    def _get_width(self) -> int:
        if self.viewport_mode == "scene":
            return self.scene_width

        return self.local_width

    def _get_height(self) -> int:
        if self.viewport_mode == "scene":
            return self.scene_height

        return self.local_height


    x = AliasProperty(
        _get_x,
        None,
        bind=[
            "viewport_mode",
            "scene_x",
            "local_x",
        ],
    )

    y = AliasProperty(
        _get_y,
        None,
        bind=[
            "viewport_mode",
            "scene_y",
            "local_y",
        ],
    )

    width = AliasProperty(
        _get_width,
        None,
        bind=[
            "viewport_mode",
            "scene_width",
            "local_width",
        ],
    )

    height = AliasProperty(
        _get_height,
        None,
        bind=[
            "viewport_mode",
            "scene_height",
            "local_height",
        ],
    )


    def _get_aspect(self) -> float:
        width = self.width
        height = self.height

        if height <= 0:
            return 1.0

        return width / height


    aspect = AliasProperty(
        _get_aspect,
        None,
        bind=[
            "width",
            "height",
        ],
    )



    __events__ = (
        "on_view_dirty",
        "on_viewport_dirty",
    )

    def __init__(
        self,
        scene: Scene,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.scene = scene
        self.view = View()

        self.view.bind(on_view_dirty=self.mark_view_dirty)

        self.scene_x = self.scene.scene_viewport_x
        self.scene_y = self.scene.scene_viewport_y
        self.scene_width = self.scene.scene_viewport_width
        self.scene_height = self.scene.scene_viewport_height

        self.scene.bind(
            scene_viewport_x=self.setter("scene_x"),
            scene_viewport_y=self.setter("scene_y"),
            scene_viewport_width=self.setter("scene_width"),
            scene_viewport_height=self.setter("scene_height"),
        )

        self.bind(
            x=self.mark_viewport_dirty,
            y=self.mark_viewport_dirty,
            width=self.mark_viewport_dirty,
            height=self.mark_viewport_dirty
        )


    # =================================== #
    # Events
    # =================================== #
    def mark_view_dirty(self, *_) -> None:
        self.dispatch("on_view_dirty")

    def mark_viewport_dirty(self, *_) -> None:
        self.dispatch("on_viewport_dirty")

    def on_view_dirty(self) -> None:
        pass

    def on_viewport_dirty(self) -> None:
        pass

    # =================================== #
    # Uitlities
    # =================================== #
    def world_to_screen(
        self,
        point: Vector3,
    ) -> tuple[float, float, float] | None:
        view = self.view

        projection = view.get_projection_matrix(self.aspect)
        view_matrix = view.get_view_matrix()

        ndc = (projection @ view_matrix).transform_point(point)

        if ndc.z < -1.0 or ndc.z > 1.0:
            return None

        x = self.x + ((ndc.x + 1.0) * 0.5 * self.width)
        y = self.y + ((ndc.y + 1.0) * 0.5 * self.height)

        return x, y, ndc.z

    def screen_to_ndc(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        local_x = x - self.x
        local_y = y - self.y

        ndc_x = (2.0 * local_x / self.width) - 1.0
        ndc_y = (2.0 * local_y / self.height) - 1.0

        return ndc_x, ndc_y

    def screen_to_ray(
        self,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        if self.view.projection_type == "orthographic":
            return self._screen_to_orthographic_ray(x, y)

        return self._screen_to_perspective_ray(x, y)

    def _screen_to_perspective_ray(
        self,
        x: float,
        y: float,
    ) -> tuple[Vector3, Vector3]:
        view = self.view
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
    ) -> tuple[Vector3, Vector3]:
        view = self.view
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

    # =================================== #
    # Helpers
    # =================================== #
    def apply(self, *_) -> None:
        glViewport(
            self.x,
            self.y,
            self.width,
            self.height,
        )

    def get_projection_matrix(self, *, uniform: bool = False):
        matrix = self.view.get_projection_matrix(self.aspect)

        if uniform:
            return matrix.to_uniform()

        return matrix

    def get_view_matrix(self, *, uniform: bool = False):
        matrix = self.view.get_view_matrix()

        if uniform:
            return matrix.to_uniform()

        return matrix

    def get_camera_position(self) -> list[float]:
        position = self.view.position

        return [
            position.x,
            position.y,
            position.z,
        ]


