# kivyfn/three/scene/base.py

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from kivy.core.window import Window
from kivy.graphics.opengl import glViewport
from kivy.graphics import (
    Callback,
    InstructionGroup
)

from kivy.input.providers.mouse import MouseMotionEvent
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

from kivyfn.ui.widget import FnWidget
from kivyfn.three.views.viewport import SceneViewport

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.controls.base import BaseController


class SceneBase(FnWidget, Widget):

    origin_x: int = NumericProperty(0)
    origin_y: int = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scene_viewport = SceneViewport()
        self._sync_scene_viewport()

        with self.canvas:
            self.render_group = InstructionGroup()
            Callback(self._restore_viewport)

        self.bind(
            x=self._sync_scene_viewport,
            y=self._sync_scene_viewport,
            width=self._sync_scene_viewport,
            height=self._sync_scene_viewport,
            origin_x=self._sync_scene_viewport,
            origin_y=self._sync_scene_viewport,
        )

    def _sync_scene_viewport(self, *_):
        self.scene_viewport.x = int(self.x + self.origin_x)
        self.scene_viewport.y = int(self.y + self.origin_y)
        self.scene_viewport.width = int(self.width)
        self.scene_viewport.height = int(self.height)

    def _restore_viewport(self, *_) -> None:
        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )



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
