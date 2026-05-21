# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path

from kivy.core.window import Window
from kivy.graphics import Callback, RenderContext
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable, glViewport
from kivy.uix.widget import Widget

from kivyfn.three.render.shader import Shader
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.cameranode import CameraNode
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.viewport import Viewport

if TYPE_CHECKING:
    from kivyfn.three.controls.base import SceneController



class Scene(Widget):
    def __init__(
        self,
        shader_path: Path,
        root: Node3D | None = None,
        camera: CameraNode | None = None,
        renderer_cls: type[Renderer] = Renderer,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.canvas = RenderContext(compute_normal_mat=True)
        self.canvas.shader.source = str(shader_path)
        self.shader = Shader(shader_path)

        self.root = root or Node3D(name="root")
        self.camera = camera or CameraNode()
        self.renderer = renderer_cls(render_ctx=self.canvas, shader=self.shader)

        self.controllers = []
        self.viewport = Viewport(self)

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

    def render(self) -> None:
        self.canvas.clear()

        self.canvas["projection_mat"] = self.camera.get_projection_matrix(self.aspect)
        self.canvas["modelview_mat"] = self.camera.get_view_matrix()

        with self.canvas:
            Callback(self.setup_gl_context)
            self.renderer.render(self.root)
            Callback(self.reset_gl_context)


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
        self.render()

    # =================================== #
    # Canvas properties
    # =================================== #
    @property
    def aspect(self) -> float:
        return (
            self.width / float(self.height)
            if self.height
            else 1.0
        )

    @property
    def modelview_mat(self):
        return self.canvas["modelview_mat"]

    @property
    def projection_mat(self):
        return self.canvas["projection_mat"]


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
    # Events
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

