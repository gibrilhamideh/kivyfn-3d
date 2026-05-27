# kivyfn/three/render/instructions_manager.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

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
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.scene.node import Node3D
    from kivyfn.three.objects.object3d import Object3D


class InstructionsManager(EventDispatcher):

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
    )

    def __init__(self) -> None:
        super().__init__()

        self.by_object: dict[int, dict[str, BaseInstructions]] = {}
        self.by_context: dict[str, dict[int, BaseInstructions]] = {}
        self.objects: dict[int, Object3D] = {}
        self._bound_objects: set[int] = set()

    def create_instructions(
        self,
        object3d: Object3D,
        ctx: RenderContext,
    ) -> BaseInstructions:
        output = getattr(ctx, "output", "color")

        if output == "depth":
            return DepthInstructions(
                geometry=object3d.geometry,
                ctx=ctx,
            )

        if output == "position":
            return PositionInstructions(
                geometry=object3d.geometry,
                ctx=ctx,
            )

        if output == "normal":
            return NormalInstructions(
                geometry=object3d.geometry,
                ctx=ctx,
            )

        if output == "object_id":
            return ObjectIdInstructions(
                geometry=object3d.geometry,
                object_id=id(object3d),
                ctx=ctx,
            )

        material = object3d.material

        if material is None:
            raise ValueError(
                f"Object {object3d.name!r} has no material for "
                f"context {ctx.name!r}."
            )

        if output == "color":
            return ColorInstructions(
                geometry=object3d.geometry,
                material=material,
                ctx=ctx,
            )

        return MaterialInstructions(
            geometry=object3d.geometry,
            material=material,
            ctx=ctx,
        )

    def attach(
        self,
        object3d: Object3D,
        ctx: RenderContext,
    ) -> BaseInstructions:
        object_id = id(object3d)
        context_name = ctx.name

        existing = self.by_object.get(object_id, {}).get(context_name)
        if existing is not None:
            return existing

        instructions = self.create_instructions(
            object3d=object3d,
            ctx=ctx,
        )

        ctx.add(instructions.group)

        self.objects[object_id] = object3d
        self.by_object.setdefault(object_id, {})[context_name] = instructions
        self.by_context.setdefault(context_name, {})[object_id] = instructions

        self.bind_object(object3d)

        return instructions

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

    def detach(
        self,
        object3d: Object3D,
        ctx: RenderContext | None = None,
    ) -> None:
        object_id = id(object3d)

        if ctx is not None:
            self._detach_one(
                object_id=object_id,
                context_name=ctx.name,
            )

            if object_id not in self.by_object:
                self.unbind_object(object3d)

            return

        for context_name in list(self.by_object.get(object_id, {})):
            self._detach_one(
                object_id=object_id,
                context_name=context_name,
            )

        self.unbind_object(object3d)
        self.objects.pop(object_id, None)

    def detach_context(
        self,
        ctx: RenderContext,
    ) -> None:
        context_name = ctx.name

        for object_id in list(self.by_context.get(context_name, {})):
            object3d = self.objects.get(object_id)

            self._detach_one(
                object_id=object_id,
                context_name=context_name,
            )

            if object3d is not None and object_id not in self.by_object:
                self.unbind_object(object3d)

        self.by_context.pop(context_name, None)

    def _detach_one(
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

        instructions.ctx.remove(instructions.group)
        instructions.destroy()

        context_objects = self.by_context.get(context_name)
        if context_objects is not None:
            context_objects.pop(object_id, None)

            if not context_objects:
                self.by_context.pop(context_name, None)

        if not context_map:
            self.by_object.pop(object_id, None)
            self.objects.pop(object_id, None)

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

    def _on_object_transform_dirty(
        self,
        object3d: Object3D,
        node: Node3D,
    ) -> None:
        self.dispatch("on_transform_dirty", node)

    def _on_object_material_dirty(
        self,
        object3d: Object3D,
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

    def clear(self) -> None:
        for object_id in list(self.by_object):
            object3d = self.objects.get(object_id)

            if object3d is not None:
                self.detach(object3d)

        self.by_object.clear()
        self.by_context.clear()
        self.objects.clear()
        self._bound_objects.clear()
