# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.core.window import Window
from kivy.graphics import Canvas
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable, glViewport
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.camera import Camera
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.viewport import Viewport
from kivyfn.three.scene.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three.render.shader import Shader
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

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

    # =================================== #
    # API
    # =================================== #
    def build(self) -> None:
        self.renderer.clear()
        self.update_camera()

        self.renderer.build(
            self.root,
            setup_gl_context=self.setup_gl_context,
            reset_gl_context=self.reset_gl_context,
        )

    def create_context(self, name: str, shader: Shader) -> RenderContext:
        return self.renderer.create_context(name, shader)

    def remove_context(self, name: str) -> None:
        self.renderer.remove_context(name)


    def add(
        self,
        child: Node3D,
        parent: Node3D | None = None,
        context: RenderContext | None = None,
    ) -> None:
        # TODO: might need to inhance this:width
        parent = parent or self.root
        parent.add_child(child)

        inherited_context = context

        if inherited_context is None and isinstance(parent, Object3D):
            inherited_context = parent.ctx

        for node in child.traverse():
            if not isinstance(node, Object3D):
                continue

            if context is not None:
                node.ctx = context
            elif node.ctx is None:
                node.ctx = inherited_context

    def remove(self, child: Node3D) -> None:
        if child.parent is not None:
            child.parent.remove_child(child)



    # =================================== #
    # gl Context
    # =================================== #
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
    def attach_controller(
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

    def detach_controller(
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

