# kivyfn/three/render/instructions_manager.py

from __future__ import annotations

from typing import Literal, Callable, TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics import Callback

from kivyfn.three.render.instructions import (
    BaseInstructions,
    ColorInstructions,
    DepthInstructions,
    MaterialInstructions,
    NormalInstructions,
    ObjectIdInstructions,
    PositionInstructions,
)

if TYPE_CHECKING:
    from kivyfn.three.render.context_manager import RenderContextManager
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.scene.node import Node3D
    from kivyfn.three.objects.object3d import Object3D


GLCallback = Callable[..., None]


RenderPassOutput = Literal[
    "depth",
    "normal",
    "position",
    "id",
    "color"
]


class InstructionsManager(EventDispatcher):

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
    )

    def __init__(
        self,
        contexts: RenderContextManager,
    ) -> None:
        super().__init__()

        self.contexts = contexts
        self.by_object: dict[int, dict[str, BaseInstructions]] = {}
        self.by_context: dict[str, dict[int, BaseInstructions]] = {}
        self.objects: dict[int, Object3D] = {}
        self._bound_objects: set[int] = set()


    # =================================== #
    # Instructions
    # =================================== #
    def create_render_instructions(
        self,
        object3d: Object3D,
        ctx: RenderContext,
    ) -> BaseInstructions:
        return MaterialInstructions(
            geometry=object3d.geometry,
            material=object3d.material,
            apply_uniform=ctx.apply_uniform,
        )

    def create_pass_instructions(
        self,
        object3d: Object3D,
        ctx: RenderContext,
        output: RenderPassOutput,
    ) -> BaseInstructions:

        if output == "depth":
            return DepthInstructions(
                geometry=object3d.geometry,
            )

        if output == "position":
            return PositionInstructions(
                geometry=object3d.geometry,
            )

        if output == "normal":
            return NormalInstructions(
                geometry=object3d.geometry,
            )

        if output == "id":
            return ObjectIdInstructions(
                geometry=object3d.geometry,
                object_id=id(object3d),
                apply_uniform=ctx.apply_uniform,
            )

        return ColorInstructions(
            geometry=object3d.geometry,
            material=object3d.material,
            apply_uniform=ctx.apply_uniform,
        )


    # =================================== #
    # Create
    # =================================== #
    def create(
        self,
        node: Node3D,
        ctx: RenderContext,
        setup_gl_context: GLCallback,
        reset_gl_context: GLCallback,
    ) -> None:
        ctx.add(Callback(setup_gl_context))

        for object3d in node.walk_objects():
            self._create(
                object3d=object3d,
                ctx=ctx,
            )

        ctx.add(Callback(reset_gl_context))

        for link in self.contexts.get_render_pass_links(ctx.name):
            pass_ctx = self.contexts.get_render_pass(link.source)

            pass_ctx.add(Callback(setup_gl_context))

            for object3d in node.walk_objects():
                self._create(
                    object3d=object3d,
                    ctx=pass_ctx,
                    output=link.output,
                )

            pass_ctx.add(Callback(reset_gl_context))


    def _create(
        self,
        object3d: Object3D,
        ctx: RenderContext,
        *,
        output: RenderPassOutput | None = None,
    ) -> BaseInstructions:
        object_id = id(object3d)
        context_name = ctx.name

        existing = self.by_object.get(object_id, {}).get(context_name)
        if existing is not None:
            return existing

        if output is None:
            instructions = self.create_render_instructions(
                object3d=object3d,
                ctx=ctx,
            )
        else:
            instructions = self.create_pass_instructions(
                object3d=object3d,
                ctx=ctx,
                output=output,
            )

        ctx.add(instructions.group)

        self.objects[object_id] = object3d
        self.by_object.setdefault(object_id, {})[context_name] = instructions
        self.by_context.setdefault(context_name, {})[object_id] = instructions

        self.bind_object(object3d)

        return instructions


    # =================================== #
    # Destroy
    # =================================== #
    def destroy(
        self,
        node: Node3D,
        ctx: RenderContext | None = None,
    ) -> None:
        for object3d in node.walk_objects():
            self._destroy(
                object3d=object3d,
                ctx=ctx,
            )

            if ctx is None:
                continue

            for link in self.contexts.get_render_pass_links(ctx.name):
                pass_ctx = self.contexts.get_render_pass(link.source)

                self._destroy(
                    object3d=object3d,
                    ctx=pass_ctx,
                )

    def _destroy(
        self,
        object3d: Object3D,
        ctx: RenderContext | None = None,
    ) -> None:
        object_id = id(object3d)

        if ctx is not None:
            self._destroy_instruction(
                object_id=object_id,
                context_name=ctx.name,
            )

            if object_id not in self.by_object:
                self.unbind_object(object3d)

            return

        for context_name in list(self.by_object.get(object_id, {})):
            self._destroy_instruction(
                object_id=object_id,
                context_name=context_name,
            )

        self.unbind_object(object3d)
        self.objects.pop(object_id, None)


    def _destroy_instruction(
        self,
        *,
        object_id: int,
        context_name: str,
    ) -> None:
        context_map = self.by_object.get(object_id)
        if context_map is None:
            return

        instructions = context_map.pop(context_name, None)
        if instructions is None:
            return

        ctx = self.contexts.get(context_name)
        ctx.remove(instructions.group)

        instructions.destroy()

        context_objects = self.by_context.get(context_name)
        if context_objects is not None:
            context_objects.pop(object_id, None)

            if not context_objects:
                self.by_context.pop(context_name, None)

        if not context_map:
            self.by_object.pop(object_id, None)
            self.objects.pop(object_id, None)


    # =================================== #
    # Visibility
    # =================================== #
    def show(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk_objects():
            for instructions in self.by_object.get(id(object3d), {}).values():
                instructions.show()

    def hide(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk_objects():
            for instructions in self.by_object.get(id(object3d), {}).values():
                instructions.hide()

    # =================================== #
    # Object Binding
    # =================================== #
    def bind_object(
        self,
        object3d: Object3D,
    ) -> None:
        object_id = id(object3d)

        if object_id in self._bound_objects:
            return

        object3d.bind(
            on_transform_dirty=self._on_object_transform_dirty,
            on_material_dirty=self._on_object_material_dirty,
        )

        self._bound_objects.add(object_id)

    def unbind_object(
        self,
        object3d: Object3D,
    ) -> None:
        object_id = id(object3d)

        if object_id not in self._bound_objects:
            return

        object3d.unbind(
            on_transform_dirty=self._on_object_transform_dirty,
            on_material_dirty=self._on_object_material_dirty,
        )

        self._bound_objects.discard(object_id)

    # =================================== #
    # Dirty Events
    # =================================== #
    def _on_object_transform_dirty(
        self,
        node: Node3D,
    ) -> None:
        self.dispatch("on_transform_dirty", node)

    def _on_object_material_dirty(
        self,
        node: Node3D,
    ) -> None:
        self.dispatch("on_material_dirty", node)

    def on_transform_dirty(
        self,
        node: Node3D,
    ) -> None:
        pass

    def on_material_dirty(
        self,
        node: Node3D,
    ) -> None:
        pass
