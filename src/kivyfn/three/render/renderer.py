# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Literal

from kivy.graphics import Canvas
from kivy.graphics.transformation import Matrix
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.context_manager import RenderContextManager
from kivyfn.three.render.instructions import MaterialInstructions
from kivyfn.three.render.instructions_manager import InstructionsManager
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.manager import LightManager


RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "material",
    "object_id",
]

GLCallback = Callable[..., None]


class Renderer(EventDispatcher):

    framerate: int | None = NumericProperty(30, allownone=True)

    def __init__(
        self,
        canvas: Canvas,
        framerate: int | None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.framerate = framerate
        self.canvas = canvas
        self.contexts = RenderContextManager()
        self.instructions = InstructionsManager()

        self.transform_dirty: set[int] = set()
        self.material_dirty: set[int] = set()

        self.instructions.bind(
            on_transform_dirty=self.queue_transform_dirty,
            on_material_dirty=self.queue_material_dirty,
        )

        self._modelview_mat: Matrix | None = None
        self._projection_mat: Matrix | None = None

    def __repr__(self) -> str:
        return (
            "Renderer("
            f"contexts={len(self.contexts)}, "
            f"instructions={len(self.instructions.by_object)}"
            ")"
        )

    # =================================== #
    # Light
    # =================================== #
    def sync_lights(self, manager: LightManager) -> None:
        raise NotImplementedError("light management not implemented yet")

    # =================================== #
    # Contexts
    # =================================== #
    def create_context(
        self,
        name: str,
        shader: Shader,
        hot_reload: bool,
        tags: set[str] | None = None,
    ) -> RenderContext:
        context = self.contexts.create(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            tags=tags,
        )

        self.canvas.add(context.ctx)
        self.sync_context_view(context)

        return context


    def hide_context(
        self,
        name: str,
    ) -> None:
        if self.contexts.hidden(name):
            return

        context = self.contexts.get(name)
        self.contexts.set_hidden(name, True)
        self.canvas.remove(context.ctx)


    def show_context(
        self,
        name: str,
    ) -> None:
        if not self.contexts.hidden(name):
            return

        context = self.contexts.get(name)

        self.contexts.set_hidden(name, False)
        self.canvas.add(context.ctx)
        self.sync_context_view(context)


    def destroy_context(
        self,
        name: str,
    ) -> None:
        hidden = self.contexts.hidden(name)
        context = self.contexts.destroy(name)

        if context is None:
            return

        self.instructions.detach_context(context)

        if not hidden:
            self.canvas.remove(context.ctx)

        context.destroy()

    # =================================== #
    # Render Pass
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
        context = self.contexts.create(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            framebuffer=True,
            size=size,
            tags=tags,
        )

        self.canvas.add(context.ctx)
        self.sync_context_view(context)

        return context


    def destroy_render_pass(
        self,
        name: str,
    ) -> None:
        self.destroy_context(name)

    def link_render_pass(
        self,
        source: str,
        uniform: str,
        *,
        output: RenderPassOutput,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> None:
        source_ctx = self.contexts.get(source)

        if not source_ctx.framebuffer:
            raise TypeError(f"Context {source!r} is not a framebuffer context.")

        texture = source_ctx.texture
        if texture is None:
            raise RuntimeError(f"Framebuffer {source!r} has no output texture.")

        slot = self.contexts.reserve_texture_slot(
            source=source,
            uniform=uniform,
            tags=tags,
            names=names,
            output=output,
        )

        for ctx in self.contexts.select(tags=tags, names=names):
            ctx.bind_texture(
                uniform=uniform,
                texture=texture,
                slot=slot,
            )


    # =================================== #
    # Build
    # =================================== #
    def add(
        self,
        node: Node3D,
        context: str,
        setup_gl_context: GLCallback,
        reset_gl_context: GLCallback,
    ) -> None:
        ctx = self.contexts.get(context)

        self.instructions.create(
            node=node,
            ctx=ctx,
            setup_gl_context=setup_gl_context,
            reset_gl_context=reset_gl_context,
        )

        self.sync_node_transform(node)
        self.sync_node_material(node)


    def hide(
        self,
        node: Node3D,
    ) -> None:
        self.instructions.hide(node)


    def show(
        self,
        node: Node3D,
    ) -> None:
        self.instructions.show(node)

    def destroy(
        self,
        node: Node3D,
    ) -> None:
        self.instructions.destroy(node)



    # =================================== #
    # Dirty Queue
    # =================================== #
    def queue_transform_dirty(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self.transform_dirty.add(id(node))
        self.flush_dirty()

    def queue_material_dirty(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self.material_dirty.add(id(node))
        self.flush_dirty()

    def flush_dirty(self, *_) -> None:
        while self.transform_dirty:
            node_id = self.transform_dirty.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_node_transform(node)

        while self.material_dirty:
            node_id = self.material_dirty.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_node_material(node)

    # =================================== #
    # Sync
    # =================================== #
    def sync_node_transform(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk_objects():
            object_id = id(object3d)
            matrix = object3d.world_matrix.to_kivy_matrix()

            for instructions in self.instructions.by_object.get(object_id, {}).values():
                instructions.sync_transform(matrix)

    def sync_node_material(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk_objects():
            object_id = id(object3d)
            material = object3d.material

            if material is None:
                continue

            for instructions in self.instructions.by_object.get(object_id, {}).values():
                if not isinstance(instructions, MaterialInstructions):
                    continue

                instructions.material = material
                instructions.sync_uniforms()
                instructions.sync_textures()

    # =================================== #
    # View
    # =================================== #
    def update_view(
        self,
        camera,
        aspect: float,
    ) -> None:
        self._projection_mat = camera.get_projection_matrix(aspect)
        self._modelview_mat = camera.get_view_matrix()

        for ctx in self.contexts.values():
            self.sync_context_view(ctx)

    def sync_context_view(
        self,
        ctx: RenderContext,
    ) -> None:
        if self._projection_mat is not None:
            ctx["projection_mat"] = self._projection_mat

        if self._modelview_mat is not None:
            ctx["modelview_mat"] = self._modelview_mat

    @property
    def modelview_mat(self) -> Matrix:
        assert self._modelview_mat is not None
        return self._modelview_mat

    @property
    def projection_mat(self) -> Matrix:
        assert self._projection_mat is not None
        return self._projection_mat
