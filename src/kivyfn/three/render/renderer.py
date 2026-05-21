# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import Callable

from kivy.graphics import Callback, Canvas
from kivy.graphics.transformation import Matrix

from kivyfn.three.render.context import RenderContext
from kivyfn.three.render.instructions import Instructions
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.object3d import Object3D


GLCallback = Callable[..., None]


class Renderer:
    def __init__(
        self,
        canvas: Canvas,
    ):
        self.canvas = canvas

        self.contexts: dict[str, RenderContext] = {}

        self._modelview_mat: Matrix | None = None
        self._projection_mat: Matrix | None = None

    def __repr__(self) -> str:
        return (
            f"Renderer("
            f"contexts={len(self.contexts)}, "
            f")"
        )

    # =================================== #
    # Contexts
    # =================================== #
    def create_context(
        self,
        name: str,
        shader: Shader,
    ) -> RenderContext:
        if name in self.contexts:
            raise ValueError(f"Render context already exists: {name!r}")

        context = RenderContext(
            name=name,
            shader=shader,
        )

        self.contexts[name] = context
        self.canvas.add(context.ctx)

        self.sync_context_view(context)

        return context

    def remove_context(
        self,
        name: str,
    ) -> None:
        context = self.contexts.pop(name, None)

        if context is None:
            return

        context.clear()

        try:
            self.canvas.remove(context.ctx)
        except ValueError:
            pass

    def get_context(
        self,
        name: str,
    ) -> RenderContext:
        return self.contexts[name]

    def clear_contexts(
        self,
    ) -> None:
        for name in list(self.contexts.keys()):
            self.remove_context(name)

    # =================================== #
    # Objects
    # =================================== #
    def add_object3d(self, object3d: Object3D):
        with object3d.ctx:
            object3d.instructions = Instructions(object3d, ctx=object3d.ctx)

    def remove_object3d(self, object3d: Object3D):
        context = object3d.ctx
        context.ctx.remove(object3d.instructions.group)

    # =================================== #
    # Build
    # =================================== #
    def clear(self):
        for ctx in self.contexts.values():
            ctx.clear()

    def build(
        self,
        root: Node3D,
        setup_gl_context: GLCallback,
        reset_gl_context: GLCallback,
    ) -> None:
        for context in self.contexts.values():
            context.clear()

            with context:
                Callback(setup_gl_context)
                self._build_node(root)
                Callback(reset_gl_context)

    def _build_node(
        self,
        node: Node3D,
    ) -> None:
        if not node.visible:
            return

        node.build(self)
        for child in node.children:
            self._build_node(child)

    def build_object(
        self,
        obj: Object3D,
    ) -> Instructions:

        return Instructions(
            object3d=obj,
            ctx=obj.ctx,
        )

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
        context: RenderContext,
    ) -> None:
        if self._projection_mat is not None:
            context.ctx["projection_mat"] = self._projection_mat

        if self._modelview_mat is not None:
            context.ctx["modelview_mat"] = self._modelview_mat

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
