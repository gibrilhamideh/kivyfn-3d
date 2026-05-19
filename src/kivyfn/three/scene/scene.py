# kivyfn/three/scene/scene.py

from __future__ import annotations

from pathlib import Path

from kivy.core.window import Window
from kivy.graphics import Callback, RenderContext
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable, glViewport
from kivy.uix.widget import Widget

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.cameranode import CameraNode
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.interaction import Interaction
from kivyfn.three.scene.viewport import Viewport



class Scene(Widget):
    def __init__(
        self,
        root_node: Node3D | None = None,
        camera: CameraNode | None = None,
        renderer: Renderer | None = None,
        shader_path: Path | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.canvas = RenderContext(compute_normal_mat=True)
        if shader_path is not None:
            self.canvas.shader.source = str(shader_path)

        self.root_node = root_node or Node3D(name="root")
        self.camera = camera or CameraNode()
        self.renderer = renderer or Renderer()

        self.interaction = Interaction(self)
        self.viewport = Viewport(self)

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

    def render(self) -> None:
        self.canvas.clear()

        self.canvas["projection_mat"] = self.camera.get_projection_matrix(self.aspect)
        self.canvas["modelview_mat"] = self.camera.get_view_matrix()

        with self.canvas:
            Callback(self.setup_gl_context)
            self.renderer.render(self.root_node)
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
    # Events
    # =================================== #
    def on_touch_down(self, touch):
        return self.interaction.on_touch_down(touch)

    def on_touch_move(self, touch):
        return self.interaction.on_touch_move(touch)

    def on_touch_up(self, touch):
        return self.interaction.on_touch_up(touch)

