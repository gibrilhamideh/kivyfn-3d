# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup

from kivyfn.three.render.context import RenderContext, RenderPass
from kivyfn.three.render.context_manager import RenderContextManager
from kivyfn.three.render.instructions import MaterialInstructions
from kivyfn.three.render.instructions_manager import InstructionsManager
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.lights.manager import LightManager
    from kivyfn.three.scene.view import View



GLCallback = Callable[..., None]


class Renderer(EventDispatcher):

    def __init__(
        self,
        canvas: InstructionGroup,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.canvas = canvas
        self.contexts = RenderContextManager()
        self.instructions = InstructionsManager(self.contexts)

        self.transform_dirty: set[int] = set()
        self.material_dirty: set[int] = set()
        self.visibility_dirty: set[int] = set()

        self.instructions.bind(
            on_transform_dirty=self.queue_transform_dirty,
            on_material_dirty=self.queue_material_dirty,
            on_visibility_dirty=self.queue_visibility_dirty
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
    def create_context(self, **kwargs) -> RenderContext:

        context = self.contexts.create_context(**kwargs)

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
    def create_render_pass(self, **kwargs) -> RenderPass:
        context = self.contexts.create_render_pass(**kwargs)

        self.canvas.add(context.ctx)
        return context

    def link_render_pass(self, **kwargs) -> None:
        self.contexts.register_render_pass_link(**kwargs)

    # =================================== #
    # Build
    # =================================== #
    def add(
        self,
        node: Node3D,
        context: str,
    ) -> None:
        ctx = self.contexts.get_context(context)

        self.instructions.create(
            node=node,
            ctx=ctx,
        )

        self.sync_node_transform(node)
        self.sync_node_material(node)

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

    def queue_visibility_dirty(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self.visibility_dirty.add(id(node))
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

        while self.visibility_dirty:
            node_id = self.visibility_dirty.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_node_visiblity(node)

    # =================================== #
    # Sync
    # =================================== #
    def sync_node_transform(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk(filter="objects"):
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
        for object3d in node.walk(filter="objects"):
            object_id = id(object3d)
            material = object3d.material
            for instructions in self.instructions.by_object.get(object_id, {}).values():
                if not isinstance(instructions, MaterialInstructions):
                    continue

                instructions.set_material(material)

    def sync_node_visiblity(
        self,
        node: Node3D,
    ) -> None:
        if node.visible_in_tree:
            self.instructions.show(node)
            return

        self.instructions.hide(node)


    # =================================== #
    # View
    # =================================== #
    def update_view(
        self,
        view: View,
        contexts: tuple[str, ...],
    ) -> None:

        for name in contexts:
            ctx = self.contexts.get(name)
            ctx.update_view(view)






