# kivyfn/three/scene/scene.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivy.properties import NumericProperty

from kivyfn.three.types import RenderPassOutput
from kivyfn.three.render.renderer import Renderer
from kivyfn.three.graph.node import Node3D
from kivyfn.three.overlays.manager import OverlayManager
from kivyfn.three.scene.base import SceneControllerBase
from kivyfn.three.scene.registry import SceneRegistry
from kivyfn.three.scene.tools import SceneTools
from kivyfn.three.types import ViewportMode

if TYPE_CHECKING:
    from kivyfn.three.views.camera import Camera
    from kivyfn.three.graphics.gl import Texture2D, TextureCube
    from kivyfn.three.render.binder import RenderBindingRecord
    from kivyfn.three.render.context import RenderContext, RenderPass2D, RenderPassCube
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
        self.renderer: Renderer
        self.overlays: OverlayManager
        self.root: Node3D
        self.registry: SceneRegistry

    def on_kv_post(self, base_widget) -> None:

        self.tools = SceneTools(self)
        self.renderer = Renderer(
            scene=self,
            canvas=self.render_group,
            max_directional_lights=self.max_directional_lights,
            max_point_lights=self.max_point_lights,
            max_spot_lights=self.max_spot_lights,
        )

        self.overlays = OverlayManager(self)
        self.registry = SceneRegistry()
        self.root = Node3D(name="root")
        self.root.scene = self # root bootstrap only

        super().on_kv_post(base_widget)


    # =================================== #
    # Context API
    # =================================== #

    def create_context(
        self,
        name: str,
        shader: Shader,
        *,
        camera: Camera | None = None,
        tags: set[str] | None = None,
        hot_reload: bool = False,
        local_x: int = 0,
        local_y: int  = 0,
        local_width: int = 1024,
        local_height: int = 1024,
        viewport_mode: ViewportMode = "scene",


    ) -> RenderContext:

        return self.renderer.create_context(
            name=name,
            camera=camera,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            local_x=local_x,
            local_y=local_y,
            local_width=local_width,
            local_height=local_height,
            viewport_mode=viewport_mode,
        )


    # =================================== #
    # Render Pass API
    # =================================== #
    def create_pass(
        self,
        name: str,
        shader: Shader,
        output: RenderPassOutput,
        output_uniform: str,
        *,
        camera: Camera | None = None,
        tags: set[str] | None = None,
        texture: Texture2D | None = None,
        size: list[int] | tuple[int, int] | int = 1024,
        push_viewport: bool = True,
        clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        clear_color_buffer: bool = True,
        clear_depth_buffer: bool = True,
        clear_stencil_buffer: bool = False,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        hot_reload: bool = False,
    ) -> RenderPass2D:
        return self.renderer.create_pass(
            name=name,
            camera=camera,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            output=output,
            output_uniform=output_uniform,
            texture=texture,
            size=size,
            push_viewport=push_viewport,
            clear_color=clear_color,
            clear_color_buffer=clear_color_buffer,
            clear_depth_buffer=clear_depth_buffer,
            clear_stencil_buffer=clear_stencil_buffer,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
        )

    def create_cube_pass(
        self,
        name: str,
        shader: Shader,
        output: RenderPassOutput,
        output_uniform: str,
        *,
        texture: TextureCube | None = None,
        tags: set[str] | None = None,
        size: list[int] | tuple[int, int] | int = 1024,
        push_viewport: bool = True,
        clear_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        clear_color_buffer: bool = True,
        clear_depth_buffer: bool = True,
        clear_stencil_buffer: bool = False,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        hot_reload: bool = False,
    ) -> RenderPassCube:
        return self.renderer.create_cube_pass(
            name=name,
            tags=tags,
            shader=shader,
            hot_reload=hot_reload,
            output=output,
            output_uniform=output_uniform,
            texture=texture,
            size=size,
            push_viewport=push_viewport,
            clear_color=clear_color,
            clear_color_buffer=clear_color_buffer,
            clear_depth_buffer=clear_depth_buffer,
            clear_stencil_buffer=clear_stencil_buffer,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
        )

    def attach_pass(
        self,
        *,
        name: str,
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
    def hide_stage(self, name: str) -> None:
        self.renderer.hide_stage(name)

    def show_stage(self, name: str) -> None:
        self.renderer.show_stage(name)

    def remove_stage(self, name: str) -> None:
        self.renderer.remove_stage(name)

    # =================================== #
    # Exports
    # =================================== #
    @property
    def stages(self):
        return self.renderer.stages


