# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.core.window import Window
from kivy.graphics import Canvas
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable, glViewport
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.camera import Camera
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.viewport import Viewport

if TYPE_CHECKING:
    from kivyfn.three.controls.base import SceneController


class Scene(Widget):

    root: Node3D = ObjectProperty(None, allownone=True)

    def __init__(self, root: Node3D | None = None, **kwargs):
        super().__init__(**kwargs)

        self.canvas = Canvas()
        self.camera = Camera()
        self.renderer = Renderer(self.canvas)
        self.viewport = Viewport(self)
        self.controllers = []

        self.root = root or Node3D(name="root")
        self.root.attach_scene(self)

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

    def render(self) -> None:
        self.renderer.clear()
        self.update_camera()

        self.renderer.render(
            self.root,
            setup_gl_context=self.setup_gl_context,
            reset_gl_context=self.reset_gl_context,
        )

    def setup_gl_context(self, *args) -> None:
        glEnable(GL_DEPTH_TEST)

        x, y = self.to_window(
            self.x,
            self.y,
        )

        glViewport(
            int(x),
            int(y),
            int(self.width),
            int(self.height),
        )

    def reset_gl_context(self, *args) -> None:
        glDisable(GL_DEPTH_TEST)

        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )

    def _on_viewport_changed(self, *args) -> None:
        self.update_camera()

    # =================================== #
    # Camera
    # =================================== #
    def update_camera(self) -> None:
        self.renderer.update_view(
            self.camera,
            self.aspect,
        )

    @property
    def aspect(self) -> float:
        return (
            self.width / float(self.height)
            if self.height
            else 1.0
        )

    @property
    def modelview_mat(self):
        return self.renderer.modelview_mat

    @property
    def projection_mat(self):
        return self.renderer.projection_mat

    # =================================== #
    # Controllers
    # =================================== #
    def attach(
        self,
        controller: SceneController,
        priority: int = 0,
    ):
        controller.attach(self)

        self.controllers.append((priority, controller))
        self.controllers.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return controller

    def detach(
        self,
        controller: SceneController,
    ) -> None:
        for item in list(self.controllers):
            _, current = item

            if current is controller:
                current.detach()
                self.controllers.remove(item)
                return

    # =================================== #
    # Touch Events
    # =================================== #
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        for _, controller in self.controllers:
            if controller.on_touch_down(touch):
                return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        for _, controller in self.controllers:
            if controller.on_touch_move(touch):
                return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        for _, controller in self.controllers:
            if controller.on_touch_up(touch):
                return True

        return super().on_touch_up(touch)

