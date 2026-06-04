# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING, Callable

from functools import partial

from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from kivy.input.providers.mouse import MouseMotionEvent
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
        ColorProperty,
        AliasProperty
)

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graph.node import Node3D
from kivyfn.three.graph.node_registry import SceneNodeRegistry
from kivyfn.three.loaders.scene_loader import SceneLoader
from kivyfn.three.lights.manager import LightManager

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.views.view_manager import ViewManager
    from kivyfn.three.render.binding_registry import RenderBindingRecord
    from kivyfn.three.render.link_registry import RenderLinkRecord
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.controls.base import SceneController
    from kivyfn.three.loaders.glb.asset import GlbSceneAsset, GlbAsset


class Scene(Widget):

    root: SceneObject = ObjectProperty()
    bg_color: tuple[float, float, float, float] = ColorProperty()

    viewport_origin_x: int = NumericProperty(0)
    viewport_origin_y: int = NumericProperty(0)

    def _get_scene_viewport_x(self):
        return int(self.x + self.viewport_origin_x)


    def _get_scene_viewport_y(self):
        return int(self.y + self.viewport_origin_y)

    def _get_scene_viewport_width(self):

        return int(self.width)

    def _get_scene_viewport_height(self):
        return int(self.height)

    scene_viewport_x: int = AliasProperty(
        _get_scene_viewport_x,
        None,
        bind=["x", "viewport_origin_x"]
    )

    scene_viewport_y: int = AliasProperty(
        _get_scene_viewport_y,
        None,
        bind=["y", "viewport_origin_y"]
    )

    scene_viewport_width: int = AliasProperty(
        _get_scene_viewport_width,
        None,
        bind=["width"]
    )

    scene_viewport_height: int = AliasProperty(
        _get_scene_viewport_height,
        None,
        bind=["height"]
    )
    

    def __init__(self, root: Node3D | None = None, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._bg_color = Color(0.0, 0.0, 0.0, 0.0)
            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        with self.canvas:

            self.group = InstructionGroup()

            Callback(self._restore_viewport)


        self.bind(
            pos=self._update_bg_rect,
            size=self._update_bg_rect,
        )

        self.loader = SceneLoader()
        self.renderer = Renderer(self.group)
        self.viewport = Viewport(self)
        self.controllers = []


        self.root = root or Node3D(name="root")
        self.nodes = SceneNodeRegistry()
        self.lights = LightManager(self.root)
        self.lights.bind(on_dirty=self.renderer.sync_lights)

        self.previews: dict[str, tuple[Color, Rectangle, Callable]] = {}


    # =================================== #
    # Context API
    # =================================== #

    def create_context(
        self,
        name: str,
        shader: Shader,
        view_name: str,
        *,
        tags: set[str] | None = None,
        hot_reload: bool = False,
        local_viewport_x: int = 0,
        local_viewport_y: int  = 0,
        local_viewport_width: int = 1024,
        local_viewport_height: int = 1024,
        use_local_viewport: bool = False,


    ) -> RenderContext:

        try:
            view = self.views.get(view_name)
        except KeyError:
            raise ValueError(
                f"Cannot create context {name!r}: "
                f"view {view_name!r} was not found."
            )

        ctx = self.renderer.create_context(
            name=name,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            local_viewport_x=local_viewport_x,
            local_viewport_y=local_viewport_y,
            local_viewport_width=local_viewport_width,
            local_viewport_height=local_viewport_height,
            use_local_viewport=use_local_viewport,
        )

        ctx.scene_viewport_x = self.scene_viewport_x
        ctx.scene_viewport_y = self.scene_viewport_y
        ctx.scene_viewport_width = self.scene_viewport_width
        ctx.scene_viewport_height = self.scene_viewport_height

        self.bind(scene_viewport_x=ctx.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=ctx.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=ctx.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=ctx.setter("scene_viewport_height"))

        self.views.link(
            view.name,
            ctx.name,
        )

        return ctx



    # =================================== #
    # Render Pass API
    # =================================== #
    def create_pass(
        self,
        name: str,
        shader: Shader,
        view_name: str,
        output: RenderPassOutput,
        output_uniform: str,
        *,
        tags: set[str] | None = None,
        color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        hot_reload: bool = False,
        local_viewport_x: int = 0,
        local_viewport_y: int  = 0,
        local_viewport_width: int = 1024,
        local_viewport_height: int = 1024,
        use_local_viewport: bool = False,
        use_viewport_size: bool = False,
        fbo_width: int = 1024,
        fbo_height: int = 1024,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        clear_color: bool = True,
        clear_depth: bool=True,
        clear_stencil: bool =False
    ) -> RenderPass:

        try:
            view = self.views.get(view_name)
        except KeyError:
            raise ValueError(
                f"Cannot create context {name!r}: "
                f"view {view_name!r} was not found."
            )

        ctx = self.renderer.create_pass(
            name=name,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            output=output,
            output_uniform=output_uniform,
            local_viewport_x=local_viewport_x,
            local_viewport_y=local_viewport_y,
            local_viewport_width=local_viewport_width,
            local_viewport_height=local_viewport_height,
            use_local_viewport=use_local_viewport,
            use_viewport_size=use_viewport_size,
            fbo_color=color,
            fbo_width=fbo_width,
            fbo_height=fbo_height,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
            clear_color=clear_color,
            clear_depth=clear_depth,
            clear_stencil=clear_stencil,
        )

        ctx.scene_viewport_x = self.scene_viewport_x
        ctx.scene_viewport_y = self.scene_viewport_y
        ctx.scene_viewport_width = self.scene_viewport_width
        ctx.scene_viewport_height = self.scene_viewport_height

        self.bind(scene_viewport_x=ctx.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=ctx.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=ctx.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=ctx.setter("scene_viewport_height"))

        self.views.link(
            view.name,
            ctx.name,
        )

        return ctx


    def attach_pass(
        self,
        *,
        pass_name: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
        index: int | None = None,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        return self.renderer.attach_pass(
            pass_name=pass_name,
            target_name=target_name,
            target_tags=target_tags,
            index=index

        )

    # =================================== #
    # Stage API
    # =================================== #
    def link_stage(
        self,
        *,
        source: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderLinkRecord | list[RenderLinkRecord]:
        return self.renderer.link_stage(
            source=source,
            target_name=target_name,
            target_tags=target_tags,
        )

    def unlink_stage(
        self,
        *,
        source: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderLinkRecord | list[RenderLinkRecord]:
        return self.renderer.unlink_stage(
            source=source,
            target_name=target_name,
            target_tags=target_tags,
        )

    def hide_stage(self, name: str) -> None:
        self.renderer.hide_stage(name)

    def show_stage(self, name: str) -> None:
        self.renderer.show_stage(name)

    def destroy_stage(self, name: str) -> None:
        self.renderer.destroy_stage(name)


    # =================================== #
    # Node Lifecycle API
    # =================================== #

    def destroy(self, node: Node3D) -> None:

        assert node.parent is not None

        for current in node.walk(filter="all"):
            self.nodes.unregister(current)

        node.parent.remove_child(node)

        self.renderer.queue_destroy(node)


    def render(
        self,
        node: Node3D,
        context: str,
        parent: Node3D | None = None,
    ) -> None:
        parent = parent or self.root
        parent.add_child(node)

        for current in node.walk(filter="all"):
            self.nodes.register(current)

        self.renderer.queue_render(node, context)


    def render_asset(
        self,
        asset: GlbAsset,
        context: str,
        *,
        parent: SceneObject | None = None,
    ) -> SceneObject:

        return self.loader.render_asset(
            self,
            asset=asset,
            context=context,
            parent=parent
        )


    def render_scene(
        self,
        scene_asset: GlbSceneAsset,
        context: str,
    ) -> list[SceneObject]:

        return self.loader.render_scene(
            self,
            scene_asset=scene_asset,
            context=context
        )

    # =================================== #
    # ViewPort
    # =================================== #
    def _restore_viewport(self, *_) -> None:
        glViewport(
            0,
            0,
            Window.width,
            Window.height,
        )

    # =================================== #
    # Exports
    # =================================== #
    @property
    def views(self) -> ViewManager:
        return self.renderer.views


    @property
    def contexts(self):
        return self.renderer.contexts

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

    # =================================== #
    # Property Events
    # =================================== #
    def on_bg_color(self, *_):
        self._bg_color.rgba = self.bg_color

    # =================================== #
    # RenderPass Helpers
    # =================================== #
    def create_render_pass_preview(
        self,
        pass_name: str,
        *,
        pos=(20, 20),
        size=(256, 256),
    ) -> None:

        ctx = self.contexts.require_pass(pass_name)

        with self.canvas.after:
            color = Color(1.0, 1.0, 1.0, 1.0)

            rect = Rectangle(
                pos=pos,
                size=size,
                texture=ctx.texture,
            )

        callback = partial(self.update_preview_texture, rect)
        ctx.bind(texture_ref=callback)
        self.previews[pass_name] = (
            color,
            rect,
            callback
        )


    def destroy_render_pass_preview(
        self,
        pass_name: str,
    ) -> None:

        ctx = self.contexts.require_pass(pass_name)

        if pass_name not in self.previews:
            raise ValueError(
                f"Render pass preview {pass_name!r} does not exist."
            )

        color, rect, callback = self.previews.pop(pass_name)
        ctx.unbind(texture_ref=callback)

        self.canvas.after.remove(color)
        self.canvas.after.remove(rect)

    def update_preview_texture(self, rect: Rectangle, ctx: RenderPass, texture: Texture):
        rect.texture = texture

    # =================================== #
    # Helpers
    # =================================== #
    def info(self) -> str:
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




