# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.graphics.opengl import GL_DEPTH_TEST, glDisable, glEnable, glViewport
from kivy.properties import ObjectProperty, ColorProperty
from kivy.uix.widget import Widget


from kivyfn.three.scene.node import Node3D
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.camera import Camera
from kivyfn.three.scene.viewport import Viewport
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.objects.material import Material
from kivyfn.three.lights.manager import LightManager

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.controls.base import SceneController
    from kivyfn.three.loaders.asset import AssetObject, SceneAsset

RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "object_id",
]


class Scene(Widget):

    root: Node3D = ObjectProperty(None, allownone=True)
    bg_color: tuple[float, float, float, float] = ColorProperty()

    def __init__(self, root: Node3D | None = None, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._bg_color = Color(0.0, 0.0, 0.0, 0.0)
            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._update_bg_rect,
            size=self._update_bg_rect,
        )

        self.camera = Camera()
        self.renderer = Renderer(self.canvas)
        self.viewport = Viewport(self)
        self.controllers = []

        self.root = root or Node3D(name="root")
        self.lights = LightManager(self.root)
        self.lights.bind(on_dirty=self.renderer.sync_lights)

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

        self.camera.bind(eye=self._on_camera_state_changed)
        self.camera.bind(target=self._on_camera_state_changed)
        self.camera.bind(up=self._on_camera_state_changed)
        self.camera.bind(fov=self._on_camera_state_changed)
        self.camera.bind(ortho_size=self._on_camera_state_changed)
        self.camera.bind(perspective=self._on_camera_state_changed)



    # =================================== #
    # Context API
    # =================================== #
    @property
    def contexts(self):
        return self.renderer.contexts

    def create_context(
        self,
        name: str,
        shader: Shader,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        return self.renderer.create_context(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            tags=tags,
        )

    def remove_context(self, name: str) -> None:
        self.renderer.remove_context(name)


    # =================================== #
    # FrameBuffer API
    # =================================== #
    def create_render_pass(
        self,
        name: str,
        shader: Shader,
        size: tuple[int, int],
        *,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        return self.renderer.create_render_pass(
            name=name,
            shader=shader,
            size=size,
            hot_reload=hot_reload,
            tags=tags,
        )

    def remove_render_pass(
        self,
        name: str,
    ) -> None:
        self.renderer.remove_render_pass(name)

    def link_re(
        self,
        source: str,
        uniform: str,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
        output: RenderPassOutput = "depth",
    ) -> None:
        self.renderer.link_render_pass(
            source=source,
            uniform=uniform,
            tags=tags,
            names=names,
            output=output,
        )

    def unlink_render_pass(
        self,
        source: str,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> None:
        self.renderer.unlink_render_pass(
            source=source,
            tags=tags,
            names=names,
        )

    # =================================== #
    # Load API
    # =================================== #
    def add(
        self,
        node: Node3D,
        context: str,
        parent: Node3D | None = None,
    ) -> None:
        parent = parent or self.root
        parent.add_child(node)

        self.renderer.add(
            node,
            context,
            setup_gl_context=self.setup_gl_context,
            reset_gl_context=self.reset_gl_context,
        )

    def remove(self, node: Node3D) -> None:
        assert node.parent is not None
        node.parent.remove_child(node)
        self.renderer.remove(node)

    def load_asset(
        self,
        asset: AssetObject,
        context: str,
        *,
        parent: Node3D | None = None,
        pickable: bool = False,
    ) -> Node3D | Object3D:

        if asset.is_renderable:
            node = Object3D(
                geometry=asset.require_geometry(),
                material=(asset.material or Material(name=asset.name)),
                name=asset.name,
                transform=asset.transform.copy(),
                pickable=pickable,
            )

        else:
            node = Node3D(
                name=asset.name,
                transform=asset.transform.copy(),
            )

        self.add(
            node,
            parent=parent,
            context=context,
        )

        for child_asset in asset.children:
            self.load_asset(
                child_asset,
                parent=node,
                context=context,
                pickable=pickable,
            )

        return node


    def load_scene(
        self,
        scene_asset: SceneAsset,
        context: str,
        *,
        pickable: bool = False,
    ) -> list[Node3D | Object3D]:

        nodes: list[Node3D] = []

        for asset in scene_asset.tree:
            node = self.load_asset(
                asset,
                context=context,
                pickable=pickable,
            )

            nodes.append(node)

        return nodes


    # =================================== #
    # gl Context
    # =================================== #
    def setup_gl_context(self, *_) -> None:
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

    def reset_gl_context(self, *_) -> None:
        glDisable(GL_DEPTH_TEST)

        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )

    def _on_viewport_changed(self, *_) -> None:
        self.update_camera()

    def _on_camera_state_changed(self, *_) -> None:
        self.update_camera()

    # =================================== #
    # 
    # =================================== #
    def _update_bg_rect(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

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

    # =================================== #
    # Property Events
    # =================================== #
    def on_bg_color(self, *_):
        self._bg_color.rgba = self.bg_color

    # =================================== #
    # Helpers
    # =================================== #
    def debug_info(self) -> str:
        return (
            "Scene(\n"
            f"  root={self.root.name!r},\n"
            f"  contexts={len(self.renderer.contexts)},\n"
            f"  controllers={len(self.controllers)},\n"
            f"  camera={self.camera.name!r},\n"
            f"  size=({self.width}, {self.height})\n"
            ")"
        )


