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

from kivyfn.three.scene.node import Node3D
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.scene.view import View
from kivyfn.three.scene.view_manager import ViewManager
from kivyfn.three.scene.viewport import Viewport
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.lights.manager import LightManager

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.controls.base import SceneController
    from kivyfn.three.loaders.asset import AssetObject, SceneAsset



class Scene(Widget):

    root: Node3D = ObjectProperty(None, allownone=True)
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

            Callback(self.restore_viewport)


        self.bind(
            pos=self._update_bg_rect,
            size=self._update_bg_rect,
        )


        self.views = ViewManager()
        self.renderer = Renderer(self.group)
        self.viewport = Viewport(self)
        self.controllers = []


        self.root = root or Node3D(name="root")
        self.lights = LightManager(self.root)
        self.lights.bind(on_dirty=self.renderer.sync_lights)


        self._next_render_id = 1
        self.by_uid: dict[str, Node3D] = {}
        self.by_render_id: dict[int, Object3D] = {}

        self.previews: dict[str, tuple[Color, Rectangle, Callable]] = {}

        self.bind(size=self._on_viewport_dirty)
        self.bind(pos=self._on_viewport_dirty)

        self.views.bind(on_view_update=self._on_view_dirty)



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
        *,
        hot_reload: bool = False,
        tags: set[str] | None = None,
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
        output: RenderPassOutput,
        *,
        color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        hot_reload: bool = False,
        tags: set[str] | None = None,
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

        ctx = self.renderer.create_render_pass(
            name=name,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            output=output,
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
        uniform_name: str,
        *,
        source_names: set[str] | None = None,
        source_tags: set[str] | None = None,
        target_names: set[str] | None = None,
        target_tags: set[str] | None = None,
        output: RenderPassOutput = "depth",
    ) -> None:
        self.renderer.link_render_pass(
            pass_name=pass_name,
            uniform_name=uniform_name,
            source_names=source_names,
            source_tags=source_tags,
            target_names=target_names,
            target_tags=target_tags,
            output=output,
        )

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
                name=asset.name,
                uid=asset.uid,
                geometry=asset.require_geometry(),
                material=asset.require_material(copy=True),
                transform=asset.transform.copy(),
                pickable=pickable,
            )

        else:
            node = Node3D(
                name=asset.name,
                uid=asset.uid,
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

        for current in node.walk(filter="all"):
            self.register_node(current)

        self.renderer.add(node, context)


    def destroy(self, node: Node3D) -> None:

        assert node.parent is not None

        for current in node.walk(filter="all"):
            self.unregister_node(current)

        node.parent.remove_child(node)

        self.renderer.destroy(node)

    # =================================== #
    # ID Handling
    # =================================== #
    def register_node(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is not None:
            if node.uid in self.by_uid:
                raise ValueError(f"Duplicate node uid: {node.uid!r}")

            self.by_uid[node.uid] = node

        if node.is_object3d(node):
            self.register_render_id(node)

    def unregister_node(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is not None:
            self.by_uid.pop(node.uid)

        if node.is_object3d(node):
            self.unregister_render_id(node)

    def register_render_id(
        self,
        object3d: Object3D,
    ) -> None:
        if object3d.render_id is None:
            object3d.render_id = self.generate_render_id()

        if object3d.render_id in self.by_render_id:
            raise ValueError(
                f"Duplicate render_id: {object3d.render_id!r}"
            )

        self.by_render_id[object3d.render_id] = object3d

    def unregister_render_id(
        self,
        object3d: Object3D,
    ) -> None:
        assert object3d.render_id is not None
        self.by_render_id.pop(object3d.render_id)

    def generate_render_id(self) -> int:
        render_id = self._next_render_id
        self._next_render_id += 1
        return render_id

    def get_by_render_id(self, render_id: int) -> Object3D | None:
        return self.by_render_id.get(render_id)

    def get_by_uid(self, uid: str) -> Node3D | Object3D | None:
        return self.by_uid.get(uid)

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

    def _on_viewport_dirty(self, *_) -> None:
        self.sync_views()

    def _on_view_dirty(
        self,
        manager: ViewManager,
        view: View,
        contexts: tuple[str, ...]
    ) -> None:
        self.update_view(view, contexts)


    # =================================== #
    # Camera
    # =================================== #
    def update_view(
        self,
        view: View, 
        names: tuple[str, ...]) -> None:
        self.renderer.update_view(view, names)

    def sync_views(self):
        for view, contexts in self.views.get_links():
            self.update_view(view, contexts)


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

        try:
            ctx = self.contexts.get_render_pass(pass_name)
        except KeyError:
            raise ValueError(
                f"Render pass {pass_name!r} does not exist."
            ) from None

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

        try:
            ctx = self.contexts.get_render_pass(pass_name)
        except KeyError:
            raise ValueError(
                f"Render pass {pass_name!r} does not exist."
            ) from None

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




