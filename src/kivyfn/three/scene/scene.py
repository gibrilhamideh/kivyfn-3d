# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Tuple

from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import (
        Color,
        Rectangle,
        Callback,
        BindTexture,
        InstructionGroup
)

from kivy.graphics.opengl import (
        glViewport,
        glGetIntegerv,
        GL_MAX_TEXTURE_IMAGE_UNITS,
        GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
)

from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        ColorProperty
)

from kivyfn.three.scene.node import Node3D
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.view import View
from kivyfn.three.scene.view_manager import ViewManager
from kivyfn.three.scene.viewport import Viewport
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.objects.material import Material
from kivyfn.three.lights.manager import LightManager

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.controls.base import SceneController
    from kivyfn.three.loaders.asset import AssetObject, SceneAsset



class Scene(Widget):

    root: Node3D = ObjectProperty(None, allownone=True)
    bg_color: tuple[float, float, float, float] = ColorProperty()
    framerate: int | None = NumericProperty(30, allownone=True)

    def __init__(self, root: Node3D | None = None, framerate: int | None = 30, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._bg_color = Color(0.0, 0.0, 0.0, 0.0)
            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        with self.canvas:
            # Callback(self.enable_depthtest)

            self.group = InstructionGroup()

            # Callback(self.disable_depthtest)
            Callback(self.restore_viewport)
            

        self.bind(
            pos=self._update_bg_rect,
            size=self._update_bg_rect,
        )


        self.views = ViewManager()
        self.renderer = Renderer(self.group, framerate)
        self.viewport = Viewport(self)
        self.controllers = []

        self.root = root or Node3D(name="root")
        self.lights = LightManager(self.root)
        self.lights.bind(on_dirty=self.renderer.sync_lights)


        self.framerate = framerate
        self.bind(framerate=self.renderer.setter("framerate"))

        self.bind(size=self._on_viewport_changed)
        self.bind(pos=self._on_viewport_changed)

        self.views.bind(on_view_update=self._on_view_udpate)



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
        view_name: str,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        # Validate that the view exists before creating/linking the context.
        view = self.views.get(view_name)

        ctx = self.renderer.create_context(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            tags=tags,
        )

        ctx.scene_x = self.x
        ctx.scene_y = self.y
        ctx.scene_width = self.width
        ctx.scene_height = self.height

        self.bind(x=ctx.setter("scene_x"))
        self.bind(y=ctx.setter("scene_y"))
        self.bind(width=ctx.setter("scene_width"))
        self.bind(height=ctx.setter("scene_height"))

        self.views.link(
            view.name,
            ctx.name,
            sync=False,
        )

        self.update_view(
            view,
            (ctx.name,),
        )

        return ctx

    def hide_context(self, name: str) -> None:
        self.renderer.hide_context(name)

    def show_context(self, name: str) -> None:
        self.renderer.show_context(name)

    def destroy_context(self, name: str) -> None:
        self.renderer.destroy_context(name)

    # =================================== #
    # FrameBuffer / Render Pass API
    # =================================== #
    def create_render_pass(
        self,
        name: str,
        shader: Shader,
        view_name: str,
        size: tuple[int, int],
        *,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderPass:
        view = self.views.get(view_name)

        ctx = self.renderer.create_render_pass(
            name=name,
            shader=shader,
            size=size,
            hot_reload=hot_reload,
            tags=tags,
        )

        ctx.scene_x = self.x
        ctx.scene_y = self.y
        ctx.scene_width = self.width
        ctx.scene_height = self.height

        self.bind(x=ctx.setter("scene_x"))
        self.bind(y=ctx.setter("scene_y"))
        self.bind(width=ctx.setter("scene_width"))
        self.bind(height=ctx.setter("scene_height"))

        self.views.link(
            view.name,
            ctx.name,
            sync=False,
        )

        self.update_view(
            view,
            (ctx.name,),
        )

        return ctx

    def link_render_pass(
        self,
        pass_name: str,
        uniform: str,
        *,
        source_names: set[str] | None = None,
        source_tags: set[str] | None = None,
        target_names: set[str] | None = None,
        target_tags: set[str] | None = None,
        output: RenderPassOutput = "depth",
    ) -> None:
        self.renderer.link_render_pass(
            pass_name=pass_name,
            uniform=uniform,
            source_names=source_names,
            source_tags=source_tags,
            target_names=target_names,
            target_tags=target_tags,
            output=output,
        )

    # =================================== #
    # Node Lifecycle API
    # =================================== #
    def add(
        self,
        node: Node3D,
        context: str,
        parent: Node3D | None = None,
    ) -> None:
        parent = parent or self.root
        parent.add_child(node)

        self.renderer.add(node, context)

    def hide(
        self,
        node: Node3D,
    ) -> None:
        self.renderer.hide(node)

    def show(
        self,
        node: Node3D,
    ) -> None:
        self.renderer.show(node)

    def destroy(self, node: Node3D) -> None:
        if node.parent is not None:
            node.parent.remove_child(node)

        self.renderer.destroy(node)

    # =================================== #
    # Load API
    # =================================== #
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
    # ViewPort
    # =================================== #
    def restore_viewport(self, *_) -> None:
        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )

    def _on_viewport_changed(self, *_) -> None:
        for view, contexts in self.views.get_links():
            self.update_view(view, contexts)

    def _on_view_udpate(
        self,
        manager: ViewManager,
        view: View,
        contexts: Tuple[str, ...]
    ) -> None:
        self.update_view(view, contexts)


    # =================================== #
    # Camera
    # =================================== #
    def update_view(
        self,
        view: View, 
        names: Tuple[str, ...]) -> None:
        self.renderer.update_view(view, names)

    def update_all_views(self,):
        pass


    # =================================== #
    # Background
    # =================================== #
    def _update_bg_rect(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size


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
            f"  size=({self.width}, {self.height})\n"
            ")"
        )

    def get_max_fragment_texture_units(self) -> int:
        value = glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)
        return value[0]


    def get_max_combined_texture_units(self) -> int:
        value = glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
        return value[0]


    def walk_instructions(
        self,
        instruction=None,
        *,
        debug: bool = False,
        level: int = 0,
    ):
        if instruction is None:
            instruction = self.canvas

        if debug:
            indent = "  " * level

            info = (
                f"{indent}- "
                f"{instruction.__class__.__name__}: "
                f"{instruction}"
            )

            if isinstance(instruction, BindTexture):
                slot = getattr(
                    instruction,
                    "index",
                    "Unknown Slot",
                )

                source = getattr(
                    instruction,
                    "source",
                    "No Source",
                )

                info += (
                    f" [Slot/Index: {slot}"
                    f" | Source: {source!r}]"
                )

            print(info)

        else:
            yield instruction, level

        if hasattr(instruction, "children"):
            for child in instruction.children:  # pyright: ignore
                if debug:
                    self.walk_instructions(
                        child,
                        debug=True,
                        level=level + 1,
                    )
                else:
                    yield from self.walk_instructions(
                        child,
                        debug=False,
                        level=level + 1,
                    )




