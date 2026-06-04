# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graph.node import Node3D
from kivyfn.three.graph.node_registry import SceneNodeRegistry
from kivyfn.three.loaders.scene_loader import SceneLoader
from kivyfn.three.lights.manager import LightManager
from kivyfn.three.scene.base import SceneControllerBase

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.views.view_manager import ViewManager
    from kivyfn.three.render.binding_registry import RenderBindingRecord
    from kivyfn.three.render.link_registry import RenderLinkRecord
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.loaders.glb.asset import GlbSceneAsset, GlbAsset


class Scene(SceneControllerBase):

    def __repr__(self) -> str:
        root = getattr(self, "root", None)

        if root is None:
            return super().__repr__()

        return (
            "Scene(\n"
            f"  root={root.name!r},\n"
            f"  contexts={len(self.stages.registry.contexts)},\n"
            f"  passes={len(self.stages.registry.passes)},\n"
            f"  nodes={len(self.nodes)},\n"
            f"  controllers={len(self.controllers)},\n"
            f"  size=({self.width}, {self.height})\n"
            ")"
        )

    def __init__(self, root: Node3D | None = None, **kwargs):
        super().__init__(**kwargs)

        self.loader = SceneLoader()
        self.renderer = Renderer(self.render_group)
        self.viewport = Viewport(self)
        self.controllers = []


        self.root = root or Node3D(name="root")
        self.nodes = SceneNodeRegistry()
        self.lights = LightManager(self.root)
        self.lights.bind(on_dirty=self.renderer.sync_lights)



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
    # Exports
    # =================================== #
    @property
    def views(self) -> ViewManager:
        return self.renderer.views


    @property
    def stages(self):
        return self.renderer.stages












