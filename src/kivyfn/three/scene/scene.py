# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.properties import NumericProperty

from kivyfn.three.render.renderer import Renderer
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graph.node import Node3D
from kivyfn.three.overlays.manager import OverlayManager
from kivyfn.three.scene.base import SceneControllerBase
from kivyfn.three.scene.registry import SceneRegistry
from kivyfn.three.scene.tools import SceneTools
from kivyfn.three.types import (
        RenderStageName,
        RenderContextName,
        RenderPassName
)

if TYPE_CHECKING:
    from kivyfn.three.views.view_manager import ViewManager
    from kivyfn.three.render.binder import RenderBindingRecord
    from kivyfn.three.render.context import RenderContext, RenderPass, RenderPassOutput
    from kivyfn.three.render.shader import Shader


class Scene(SceneControllerBase):

    max_directional_lights: int = NumericProperty(1)
    max_spot_lights: int = NumericProperty(5)
    max_point_lights: int = NumericProperty(5)

    def __repr__(self) -> str:
        root = getattr(self, "root", None)
        nodes = getattr(self, "nodes", None)
        stages = getattr(self, "stages", None)
        controllers = getattr(self, "controllers", None)

        if root is None or nodes is None or stages is None or controllers is None:
            return super().__repr__()

        return (
            "Scene(\n"
            f"  root={root.name!r},\n"
            f"  contexts={len(stages.registry.contexts)},\n"
            f"  passes={len(stages.registry.passes)},\n"
            f"  nodes={len(nodes)},\n"
            f"  controllers={len(controllers)},\n"
            f"  size=({self.width}, {self.height})\n"
            ")"
        )

    def __init__(
            self,
            *,
            max_directional_lights: int = 1,
            max_point_lights: int = 5,
            max_spot_lights: int = 5,
            **kwargs):
        super().__init__(
            max_directional_lights=max_directional_lights,
            max_point_lights=max_point_lights,
            max_spot_lights=max_spot_lights,
            **kwargs)

        self.tools: SceneTools
        self.viewport: Viewport
        self.renderer: Renderer
        self.overlays: OverlayManager
        self.root: Node3D
        self.registry: SceneRegistry

    def on_kv_post(self, base_widget) -> None:

        self.tools = SceneTools(self)
        self.viewport = Viewport(self)
        self.renderer = Renderer(
            self.render_group,
            max_directional_lights=self.max_directional_lights,
            max_point_lights=self.max_point_lights,
            max_spot_lights=self.max_spot_lights,
        )

        self.overlays = OverlayManager(self)
        self.registry = SceneRegistry()
        self.root = Node3D(name="root")
        self.root.scene = self # root bootstrap only

        self.bind(scene_viewport_x=self.renderer.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=self.renderer.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=self.renderer.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=self.renderer.setter("scene_viewport_height"))
        super().on_kv_post(base_widget)


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
    def hide_stage(self, name: RenderStageName) -> None:
        self.renderer.hide_stage(name)

    def show_stage(self, name: RenderStageName) -> None:
        self.renderer.show_stage(name)

    def destroy_stage(self, name: RenderStageName) -> None:
        self.renderer.destroy_stage(name)

    # =================================== #
    # Exports
    # =================================== #
    @property
    def views(self) -> ViewManager:
        return self.renderer.views

    @property
    def stages(self):
        return self.renderer.stages


