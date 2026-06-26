# kivyfn/three/render/stages.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivyfn.three.render.stage import RenderStage
from kivyfn.three.render.registry import RenderStageRegistry
from kivyfn.three.render.binder import (
    RenderBindingRecord,
    RenderBindingRegistry,
    RenderBinderManager,
    RenderBindingGraph,
)
from kivyfn.three.graphics.gl import (
    Texture2D,
    TextureCube,
)
from kivyfn.three.graphics.gl.targets import (
    ScreenTarget,
    Texture2DTarget,
    TextureCubeTarget,
)
from kivyfn.three.graphics.gl.utils import normalize_size
from kivyfn.three.views.view import View
from kivyfn.three.views.viewport import (
    Viewport,
    LocalViewport,
)
from kivyfn.three.types import Color, ViewportSource

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.camera import Camera
    from kivyfn.three.render.shader import Shader


class RenderStageManager:

    def __init__(self) -> None:
        self.registry = RenderStageRegistry()

        self.bindings = RenderBindingRegistry(
            registry=self.registry,
        )

        self.binder_manager = RenderBinderManager(
            stage_registry=self.registry,
            binding_registry=self.bindings,
        )

    def __len__(self) -> int:
        return len(self.registry)

    # =================================== #
    # General API
    # =================================== #

    def add(
        self,
        stage: RenderStage,
        tags: set[str] | None = None,
    ) -> RenderStage:
        self.registry.register(stage)

        if tags is not None:
            for tag in tags:
                self.registry.tag(stage.name, tag)

        return stage

    def remove(
        self,
        name: str,
    ) -> RenderStage:
        self.registry.require(name)

        graph = self.removal_plan(name)
        if graph.dependents:
            dependents = ", ".join(sorted(graph.dependents))

            raise RuntimeError(
                f"Cannot remove render stage {name!r} because it is "
                f"required by: {dependents}."
            )

        for record in list(self.bindings.incoming(name) or ()):
            self.binder_manager.detach(record)
            self.bindings.remove(record)

        return self.registry.unregister(name)

    def removal_plan(
        self,
        name: str,
    ) -> RenderBindingGraph:
        return self.bindings.graph_of(name)

    # =================================== #
    # Stage Creation
    # =================================== #

    def create_screen_stage(
        self,
        *,
        scene: Scene,
        name: str,
        shader: Shader,
        camera: Camera | None = None,
        tags: set[str] | None = None,
        hot_reload: bool = False,
        depth_test: bool = True,
        local_x: int = 0,
        local_y: int = 0,
        local_width: int = 1024,
        local_height: int = 1024,
        viewport_source: ViewportSource = "scene",
    ) -> RenderStage:
        view = self._create_view(camera)

        viewport = self._create_viewport(
            scene=scene,
            local_x=local_x,
            local_y=local_y,
            local_width=local_width,
            local_height=local_height,
            viewport_source=viewport_source,
        )

        target = ScreenTarget(
            view=view,
            viewport=viewport,
            depth_test=depth_test,
        )

        stage = RenderStage(
            name=name,
            shader=shader,
            target=target,
            hot_reload=hot_reload,
        )

        return self.add(
            stage,
            tags=tags,
        )


    def create_texture_2d_stage(
        self,
        *,
        scene: Scene,
        name: str,
        shader: Shader,
        attach_as: str,
        camera: Camera | None = None,
        tags: set[str] | None = None,
        texture: Texture2D | None = None,
        size: int | tuple[int, int] | list[int] = 1024,
        hot_reload: bool = False,
        depth_test: bool = True,
        push_viewport: bool = True,
        viewport_source: ViewportSource = "local",
        clear_color: Color = (0.0, 0.0, 0.0, 0.0),
        clear_color_buffer: bool = True,
        clear_depth_buffer: bool = True,
        clear_stencil_buffer: bool = False,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
    ) -> RenderStage:
        width, height = normalize_size(size)

        if texture is None:
            texture = Texture2D.empty(
                size=(width, height),
            )

        if texture.size != (width, height):
            raise ValueError(
                f"Texture2D size {texture.size!r} does not match "
                f"stage size {(width, height)!r}."
            )

        view = self._create_view(camera)

        viewport = self._create_viewport(
            scene=scene,
            local_x=0,
            local_y=0,
            local_width=width,
            local_height=height,
            viewport_source=viewport_source,
        )

        target = Texture2DTarget(
            view=view,
            viewport=viewport,
            texture=texture,
            size=(width, height),
            attach_as=attach_as,
            clear_color=clear_color,
            clear_color_buffer=clear_color_buffer,
            clear_depth_buffer=clear_depth_buffer,
            clear_stencil_buffer=clear_stencil_buffer,
            depth_test=depth_test,
            push_viewport=push_viewport,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
        )

        stage = RenderStage(
            name=name,
            shader=shader,
            target=target,
            hot_reload=hot_reload,
        )

        return self.add(
            stage,
            tags=tags,
        )


    def create_texture_cube_stage(
        self,
        *,
        scene: Scene,
        name: str,
        shader: Shader,
        attach_as: str,
        tags: set[str] | None = None,
        texture: TextureCube | None = None,
        size: int | tuple[int, int] | list[int] = 1024,
        hot_reload: bool = False,
        depth_test: bool = True,
        push_viewport: bool = True,
        viewport_source: ViewportSource = "local",
        clear_color: Color = (0.0, 0.0, 0.0, 0.0),
        clear_color_buffer: bool = True,
        clear_depth_buffer: bool = True,
        clear_stencil_buffer: bool = False,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
    ) -> RenderStage:
        width, height = normalize_size(size)

        if width != height:
            raise ValueError(
                f"Texture cube stage size must be square, got {width}x{height}."
            )

        if texture is None:
            texture = TextureCube.empty(
                size=(width, height),
            )

        if texture.size != (width, height):
            raise ValueError(
                f"TextureCube size {texture.size!r} does not match "
                f"stage size {(width, height)!r}."
            )

        view = self._create_cube_view()

        viewport = self._create_viewport(
            scene=scene,
            local_x=0,
            local_y=0,
            local_width=width,
            local_height=height,
            viewport_source=viewport_source,
        )

        target = TextureCubeTarget(
            view=view,
            viewport=viewport,
            texture=texture,
            size=(width, height),
            attach_as=attach_as,
            clear_color=clear_color,
            clear_color_buffer=clear_color_buffer,
            clear_depth_buffer=clear_depth_buffer,
            clear_stencil_buffer=clear_stencil_buffer,
            depth_test=depth_test,
            push_viewport=push_viewport,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
        )

        stage = RenderStage(
            name=name,
            shader=shader,
            target=target,
            hot_reload=hot_reload,
        )

        return self.add(
            stage,
            tags=tags,
        )

    # =================================== #
    # Stage Output Binding
    # =================================== #

    def attach_output(
        self,
        *,
        name: str,
        target_name: str | None = None,
        target_tags: set[str] | None = None,
        index: int | None = None,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        if target_name is None and not target_tags:
            raise ValueError(
                "bind_stage_output() requires either 'target_name' or "
                "'target_tags'."
            )

        if target_name is not None and target_tags:
            raise ValueError(
                "bind_stage_output() accepts either 'target_name' or "
                "'target_tags', not both."
            )

        self.registry.require_output_stage(name)

        if target_name is not None:
            return self.binder_manager.attach(
                source_name=name,
                target_name=target_name,
                index=index,
            )

        if index is not None:
            raise ValueError(
                "bind_stage_output() cannot use a fixed texture index when "
                "binding to multiple targets by tag."
            )

        assert target_tags is not None

        targets: dict[str, RenderStage] = {}

        for tag in target_tags:
            for target in self.registry.stages_of(tag):
                targets[target.name] = target

        return [
            self.binder_manager.attach(
                source_name=name,
                target_name=target.name,
            )
            for target in targets.values()
        ]

    # =================================== #
    # Dependency API
    # =================================== #

    def dependencies_of(
        self,
        name: str,
    ) -> set[str]:
        bound = self.bindings.dependencies_of(name)

        return set(bound or ())

    def dependents_of(
        self,
        name: str,
    ) -> set[str]:
        bound = self.bindings.dependents_of(name)

        return set(bound or ())

    def graph_of(
        self,
        name: str,
    ) -> RenderBindingGraph:
        return self.bindings.graph_of(name)

    # =================================== #
    # Uniform API
    # =================================== #

    def set_uniform(
        self,
        name: str,
        uniform: str,
        value: Any,
    ) -> None:
        stage = self.registry.require(name)
        stage.apply_uniform(
            uniform,
            value,
        )

    def set_uniform_by_tag(
        self,
        tag: str,
        uniform: str,
        value: Any,
    ) -> None:
        for stage in self.registry.stages_of(tag):
            stage.apply_uniform(
                uniform,
                value,
            )

    # =================================== #
    # Internals
    # =================================== #

    def _create_view(
        self,
        camera: Camera | None,
    ) -> View:
        view = View()
        if camera is not None:
            return camera.attach(view)

        return view

    def _create_cube_view(
        self,
    ) -> View:
        view = View()
        view.projection = "perspective"
        view.fov = 90.0
        return view

    def _create_viewport(
        self,
        *,
        scene: Scene,
        local_x: int,
        local_y: int,
        local_width: int,
        local_height: int,
        viewport_source: ViewportSource,
    ) -> Viewport:
        local_viewport = LocalViewport()
        local_viewport.x = local_x
        local_viewport.y = local_y
        local_viewport.width = local_width
        local_viewport.height = local_height

        return Viewport(
            scene_viewport=scene.scene_viewport,
            local_viewport=local_viewport,
            source=viewport_source,
        )


