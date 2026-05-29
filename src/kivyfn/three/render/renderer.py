# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Literal

from kivy.event import EventDispatcher
from kivy.graphics import Canvas
from kivy.graphics.transformation import Matrix
from kivy.properties import NumericProperty

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.context_manager import RenderContextManager
from kivyfn.three.render.instructions import MaterialInstructions
from kivyfn.three.render.instructions_manager import InstructionsManager
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.manager import LightManager
    from kivyfn.three.scene.view import View


RenderPassOutput = Literal[
    "depth",
    "normal",
    "position",
    "id",
    "color"
]

GLCallback = Callable[..., None]


class Renderer(EventDispatcher):

    framerate: int | None = NumericProperty(30, allownone=True)

    def __init__(
        self,
        canvas: Canvas,
        framerate: int | None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.framerate = framerate
        self.canvas = canvas
        self.contexts = RenderContextManager()
        self.instructions = InstructionsManager(self.contexts)

        self.transform_dirty: set[int] = set()
        self.material_dirty: set[int] = set()

        self.instructions.bind(
            on_transform_dirty=self.queue_transform_dirty,
            on_material_dirty=self.queue_material_dirty,
        )

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
        context = self.contexts.create_context(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            tags=tags,
        )

        self.canvas.add(context.ctx)

        return context

    def hide_context(
        self,
        name: str,
    ) -> None:
        if self.contexts.context_hidden(name):
            return

        context = self.contexts.get_context(name)

        self.contexts.hide_context(name)
        self.canvas.remove(context.ctx)

    def show_context(
        self,
        name: str,
    ) -> None:
        if not self.contexts.context_hidden(name):
            return

        context = self.contexts.get_context(name)

        self.contexts.show_context(name)
        self.canvas.add(context.ctx)

    def destroy_context(
        self,
        name: str,
    ) -> None:
        hidden = self.contexts.context_hidden(name)
        context = self.contexts.destroy_context(name)

        if context is None:
            return

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
        context = self.contexts.create_render_pass(
            name=name,
            shader=shader,
            size=size,
            hot_reload=hot_reload,
            tags=tags,
        )

        self.canvas.add(context.ctx)

        return context

    def link_render_pass(
        self,
        source: str,
        uniform: str,
        *,
        output: RenderPassOutput,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> None:
        source_ctx = self.contexts.get_render_pass(source)

        texture = source_ctx.texture
        if texture is None:
            raise RuntimeError(f"Render pass {source!r} has no output texture.")

        targets = self.contexts.select_contexts(
            tags=tags,
            names=names,
        )

        for target_ctx in targets:
            link = self.contexts.register_render_pass_link(
                target=target_ctx.name,
                source=source,
                output=output,
                uniform=uniform,
            )

            target_ctx.bind_texture(
                uniform=uniform,
                texture=texture,
                slot=link.slot,
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
        ctx = self.contexts.get_context(context)

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

            model_mat = object3d.world_matrix
            normal_mat = model_mat.compute_normal_matrix()

            for instructions in self.instructions.by_object.get(
                object_id,
                {},
            ).values():
                instructions.sync_transform(
                    model_mat=model_mat,
                    normal_mat=normal_mat,
                )

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
        view: View,
        contexts: tuple[str, ...],
        aspect: float,
    ) -> None:
        projection_mat = view.get_projection_matrix(aspect)
        view_mat = view.get_view_matrix()

        for name in contexts:
            ctx = self.contexts.get(name)
            self.sync_context_view(
                ctx,
                projection_mat,
                view_mat,
            )

    def sync_context_view(
        self,
        ctx: RenderContext,
        projection_mat: Matrix,
        view_mat: Matrix,
    ) -> None:
        ctx["projection_mat"] = projection_mat
        ctx["view_mat"] = view_mat


