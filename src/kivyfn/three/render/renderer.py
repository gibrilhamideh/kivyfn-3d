# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import Literal, Callable, TYPE_CHECKING

from kivy.graphics import Callback, Canvas
from kivy.graphics.transformation import Matrix

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.manager import RenderContextManager
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.manager import LightManager

FramebufferOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "object_id",
]

GLCallback = Callable[..., None]


class Renderer:
    def __init__(
        self,
        canvas: Canvas,
    ):
        self.canvas = canvas
        self.contexts = RenderContextManager()

        self._modelview_mat: Matrix | None = None
        self._projection_mat: Matrix | None = None

    def __repr__(self) -> str:
        return (
            f"Renderer("
            f"contexts={len(self.contexts)}, "
            f")"
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
        context = RenderContext(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
        )

        self.contexts.add(
            name=name,
            context=context,
            tags=tags,
        )

        self.canvas.add(context.ctx)
        self.sync_context_view(context)

        return context

    def remove_context(
        self,
        name: str,
    ) -> None:
        context = self.contexts.remove(name)

        if context is None:
            return

        context.destroy()
        self.canvas.remove(context.ctx)


    def clear_contexts(
        self,
    ) -> None:
        for name in self.contexts.names():
            self.remove_context(name)


    # =================================== #
    # FrameBuffer
    # =================================== #
    def create_framebuffer(
        self,
        name: str,
        shader: Shader,
        size: tuple[int, int],
        *,
        hot_reload: bool = False,
        tags: set[str] | None = None,
    ) -> RenderContext:
        context = RenderContext(
            name=name,
            shader=shader,
            hot_reload=hot_reload,
            framebuffer=True,
            size=size,
        )

        self.contexts.add(
            name=name,
            context=context,
            tags=tags,
        )

        self.canvas.add(context.ctx)
        self.sync_context_view(context)

        return context

    def remove_framebuffer(
        self,
        name: str,
    ) -> None:
        self.unlink_framebuffer(source=name)
        self.remove_context(name)

    def link_framebuffer(
        self,
        source: str,
        uniform: str,
        *,
        output: FramebufferOutput = "color",
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
            output=output
        )

        for ctx in self.contexts.select(tags=tags, names=names):
            ctx.bind_texture(
                uniform=uniform,
                texture=texture,
                slot=slot,
            )

    def unlink_framebuffer(
        self,
        source: str,
        *,
        tags: set[str] | None = None,
        names: set[str] | None = None,
    ) -> None:
        links = self.contexts.release_texture_links(
            source=source,
            tags=tags,
            names=names,
        )

        for link in links:
            for ctx in self.contexts.select(
                tags=link.tags,
                names=link.names,
            ):
                ctx.unbind_texture(link.uniform)

    # =================================== #
    # Build
    # =================================== #
    def clear(self) -> None:
        for ctx in self.contexts.values():
            ctx.clear()

    def remove(self, node: Node3D) -> None:
        self.detach(node)

    def add(
        self,
        node: Node3D,
        context: str,
        setup_gl_context: GLCallback,
        reset_gl_context: GLCallback,
    ) -> None:
        ctx = self.contexts.get(context)

        with ctx:
            Callback(setup_gl_context)
            self.attach(node, ctx)
            Callback(reset_gl_context)

    def attach(
        self,
        node: Node3D,
        ctx: RenderContext,
    ) -> None:
        for child in node.walk_tree():
            child.attach(ctx)

    def detach(
        self,
        node: Node3D,
    ) -> None:
        for child in node.walk_tree():
            child.detach()

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
    def modelview_mat(
        self,
    ) -> Matrix:
        assert self._modelview_mat is not None
        return self._modelview_mat

    @property
    def projection_mat(
        self,
    ) -> Matrix:
        assert self._projection_mat is not None
        return self._projection_mat
