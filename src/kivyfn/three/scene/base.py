# kivyfn/three/scene/base.py

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from kivy.core.window import Window
from kivy.graphics.opengl import glViewport
from kivy.graphics import (
    Color,
    Rectangle,
    Callback,
    InstructionGroup
)

from kivy.input.providers.mouse import MouseMotionEvent
from kivy.properties import (
    AliasProperty,
    ColorProperty,
    NumericProperty,
)
from kivy.uix.widget import Widget

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.controls.base import BaseController


class SceneBase(Widget):
    bg_color: tuple[float, float, float, float] = ColorProperty(
        (0.0, 0.0, 0.0, 0.0)
    )

    viewport_origin_x: int = NumericProperty(0)
    viewport_origin_y: int = NumericProperty(0)

    def _get_scene_viewport_x(self) -> int:
        return int(self.x + self.viewport_origin_x)

    def _get_scene_viewport_y(self) -> int:
        return int(self.y + self.viewport_origin_y)

    def _get_scene_viewport_width(self) -> int:
        return int(self.width)

    def _get_scene_viewport_height(self) -> int:
        return int(self.height)

    scene_viewport_x: int = AliasProperty(
        _get_scene_viewport_x,
        None,
        bind=["x", "viewport_origin_x"],
    )

    scene_viewport_y: int = AliasProperty(
        _get_scene_viewport_y,
        None,
        bind=["y", "viewport_origin_y"],
    )

    scene_viewport_width: int = AliasProperty(
        _get_scene_viewport_width,
        None,
        bind=["width"],
    )

    scene_viewport_height: int = AliasProperty(
        _get_scene_viewport_height,
        None,
        bind=["height"],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._bg_color = Color(*self.bg_color)
            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        with self.canvas:
            self.render_group = InstructionGroup()
            Callback(self._restore_viewport)

        self.bind(
            pos=self._update_bg_rect,
            size=self._update_bg_rect,
        )

    def _restore_viewport(self, *_) -> None:
        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )

    def _update_bg_rect(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_bg_color(self, *_):
        self._bg_color.rgba = self.bg_color


class SceneControllerBase(SceneBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controllers: list[tuple[int, BaseController]] = []

    def attach_controller(
        self,
        controller: BaseController,
        priority: int = 0,
    ) -> BaseController:
        scene = cast("Scene", self)
        controller.attach(scene)

        self.controllers.append((priority, controller))
        self.controllers.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return controller

    def detach_controller(
        self,
        controller: BaseController,
    ) -> None:
        for item in list(self.controllers):
            _, current = item

            if current is controller:
                current.detach()
                self.controllers.remove(item)
                return

    def on_touch_down(self, touch: MouseMotionEvent):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        for _, controller in self.controllers:
            if controller.on_touch_down(touch):
                return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch: MouseMotionEvent):
        for _, controller in self.controllers:
            if controller.on_touch_move(touch):
                return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch: MouseMotionEvent):
        for _, controller in self.controllers:
            if controller.on_touch_up(touch):
                return True

        return super().on_touch_up(touch)
