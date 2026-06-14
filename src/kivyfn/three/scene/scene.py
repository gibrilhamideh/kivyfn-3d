# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graph.node import Node3D
from kivyfn.three.graph.node_registry import SceneNodeRegistry
from kivyfn.three.loaders.scene_loader import SceneLoader
from kivyfn.three.scene.base import SceneControllerBase
from kivyfn.three.overlays.manager import OverlayManager
from kivyfn.three.scene.tools import SceneTools
from kivyfn.three.types import (
        SceneObject,
        SceneBlueprint,
        AssetBlueprint,
        RenderStageName,
        RenderContextName,
        RenderPassName
)

if TYPE_CHECKING:
    from kivyfn.three.views.view_manager import ViewManager
    from kivyfn.three.render.binding_registry import RenderBindingRecord
    from kivyfn.three.render.link_registry import RenderLinkRecord
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader


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

    def __init__(
            self,
            root: Node3D | None = None,
            *,
            max_directional_lights: int = 1,
            max_point_lights: int = 5,
            max_spot_lights: int = 5,
            **kwargs):
        super().__init__(**kwargs)

        self.loader = SceneLoader()
        self.tools = SceneTools(self)
        self.viewport = Viewport(self)
        self.renderer = Renderer(
            self.render_group,
            max_directional_lights=max_directional_lights,
            max_point_lights=max_point_lights,
            max_spot_lights=max_spot_lights,
        )

        self.overlays = OverlayManager(self)
        self.root = root or Node3D(name="root")
        self.nodes = SceneNodeRegistry()

        self.bind(scene_viewport_x=self.renderer.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=self.renderer.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=self.renderer.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=self.renderer.setter("scene_viewport_height"))


    # =================================== #
    # Context API
    # =================================== #

    def create_context(
        self,
        name: RenderContextName,
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

        return self.renderer.create_context(
            name=name,
            view_name=view_name,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            local_viewport_x=local_viewport_x,
            local_viewport_y=local_viewport_y,
            local_viewport_width=local_viewport_width,
            local_viewport_height=local_viewport_height,
            use_local_viewport=use_local_viewport,
        )


    # =================================== #
    # Render Pass API
    # =================================== #
    def create_pass(
        self,
        name: RenderPassName,
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
        size_to_viewport: bool = False,
        fbo_width: int = 1024,
        fbo_height: int = 1024,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        clear_color: bool = True,
        clear_depth: bool=True,
        clear_stencil: bool =False
    ) -> RenderPass:

        return self.renderer.create_pass(
            name=name,
            view_name=view_name,
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
            size_to_viewport=size_to_viewport,
            fbo_color=color,
            fbo_width=fbo_width,
            fbo_height=fbo_height,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
            clear_color=clear_color,
            clear_depth=clear_depth,
            clear_stencil=clear_stencil,
        )


    def attach_pass(
        self,
        *,
        name: RenderPassName,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
        index: int | None = None,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        return self.renderer.attach_pass(
            name=name,
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
        source: RenderStageName,
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
        source: RenderStageName,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
    ) -> RenderLinkRecord | list[RenderLinkRecord]:
        return self.renderer.unlink_stage(
            source=source,
            target_name=target_name,
            target_tags=target_tags,
        )

    def hide_stage(self, name: RenderStageName) -> None:
        self.renderer.hide_stage(name)

    def show_stage(self, name: RenderStageName) -> None:
        self.renderer.show_stage(name)

    def destroy_stage(self, name: RenderStageName) -> None:
        self.renderer.destroy_stage(name)


    # =================================== #
    # Node Lifecycle API
    # =================================== #

    def destroy(self, node: Node3D) -> None:

        assert node.parent is not None

        for current in node.walk(filter="all"):
            self.nodes.unregister(current)

        node.parent.remove_child(node)

        self.overlays.detach_by_subtree(node)
        self.renderer.queue_destroy(node)


    def render(
        self,
        node: Node3D,
        *,
        stage: RenderStageName | None = None,
        stages: list[RenderStageName] | None = None,
        parent: Node3D | None = None,
    ) -> None:

        if stage is not None and stages is not None:
            raise ValueError(
                "Provide either 'stage' or 'stages', not both."
            )

        if stage is None and stages is None:
            raise ValueError(
                "Either 'stage' or 'stages' must be provided."
            )

        parent = parent or self.root
        parent.add_child(node)

        for current in node.walk(filter="all"):
            self.nodes.register(current)

        self.renderer.queue_render(
            node,
            stage=stage,
            stages=stages,
        )


    def render_blueprint(
        self,
        blueprint: AssetBlueprint,
        stage_name: str,
        *,
        parent: SceneObject | None = None,
    ) -> SceneObject:

        return self.loader.render_blueprint(
            self,
            blueprint=blueprint,
            stage_name=stage_name,
            parent=parent
        )


    def render_scene_blueprint(
        self,
        scene_blueprint: SceneBlueprint,
        stage_name: str,
    ) -> list[SceneObject]:

        return self.loader.render_scene_blueprint(
            self,
            scene_blueprint=scene_blueprint,
            stage_name=stage_name
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


