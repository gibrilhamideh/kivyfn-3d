# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, Literal
from dataclasses import dataclass
from collections import deque

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup

from kivyfn.three.render.view_manager import ViewManager
from kivyfn.three.render.context_manager import RenderContextManager
from kivyfn.three.render.instructions_manager import InstructionsManager
from kivyfn.three.render.instructions import MaterialInstructions


if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext, RenderPass
    from kivyfn.three.scene.node import Node3D
    from kivyfn.three.render.view import View
    from kivyfn.three.render.binder_registry import RenderBinderRecord
    from kivyfn.three.render.link_registry import RenderLinkRecord
    from kivyfn.three.lights.manager import LightManager

RenderStage: TypeAlias = "RenderPass | RenderContext"

@dataclass(slots=True)
class RenderCommand:
    op: Literal["render", "destroy"]
    node: Node3D
    context: str | None = None

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
        self.views = ViewManager()

        self.views.bind(
            on_view_dirty=lambda _, view, name: self.queue_view(
                view,
                name,
            )
        )

        self.instructions.bind(
            on_transform_dirty=self.queue_transform,
            on_material_dirty=self.queue_material,
            on_visibility_dirty=self.queue_visibility
        )

        self.hidden: set[str] = set()

        self._lifecycle_queue: deque[RenderCommand] = deque()
        self._transform_queue: set[int] = set()
        self._material_queue: set[int] = set()
        self._visibility_queue: set[int] = set()
        self._viewport_queue: set[str] = set()
        self._view_queue: dict[str, View] = {}

        self._trigger_dirty = Clock.create_trigger(self.flush_dirty, -1)

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
        context.bind(on_viewport_dirty=self.queue_viewport)

        self.canvas.add(context.ctx)
        return context


    # =================================== #
    # Render Pass
    # =================================== #
    def create_pass(self, **kwargs) -> RenderPass:

        context = self.contexts.create_pass(**kwargs)
        context.bind(on_viewport_dirty=self.queue_viewport)

        self.canvas.add(context.ctx)
        return context

    def attach_pass(self, **kwargs) -> RenderBinderRecord | list[RenderBinderRecord]:

        return self.contexts.attach_pass(**kwargs)

    # =================================== #
    # Shared
    # =================================== #
    def link_stage(self, **kwargs) -> RenderLinkRecord | list[RenderLinkRecord]:

        return self.contexts.link(**kwargs)

    def unlink_stage(self, **kwargs) -> RenderLinkRecord | list[RenderLinkRecord]:

        return self.contexts.unlink(**kwargs)

    def hide_stage(
        self,
        name: str,
    ) -> None:

        if name in self.hidden:
            return

        stage = self.contexts.require(name)
        self.canvas.remove(stage.ctx)
        self.hidden.add(name)

    def show_stage(
        self,
        name: str,
    ) -> None:

        if name not in self.hidden:
            return

        stage = self.contexts.require(name)
        self.canvas.add(stage.ctx)
        self.hidden.remove(name)

    def destroy_stage(
        self,
        name: str,
    ) -> None:

        if name not in self.hidden:
            stage = self.contexts.require(name)
            self.canvas.remove(stage.ctx)

        self.contexts.destroy(name)

    # =================================== #
    # Dirty Queue
    # =================================== #
    def queue_render(
        self,
        node: Node3D,
        context: str,
    ) -> None:

        self._lifecycle_queue.append(
            RenderCommand(
                op="render",
                node=node,
                context=context,
            )
        )
        self._trigger_dirty()


    def queue_destroy(
        self,
        node: Node3D,
    ) -> None:
        self._lifecycle_queue.append(
            RenderCommand(
                op="destroy",
                node=node,
            )
        )
        self._trigger_dirty()

    def queue_transform(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self._transform_queue.add(id(node))
        self._trigger_dirty()

    def queue_material(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self._material_queue.add(id(node))
        self._trigger_dirty()

    def queue_visibility(
        self,
        manager: InstructionsManager,
        node: Node3D,
    ) -> None:
        self._visibility_queue.add(id(node))
        self._trigger_dirty()

    def queue_view(
            self,
            view: View,
            context: str
    ) -> None:
        self._view_queue[context] = view
        self._trigger_dirty()

    def queue_viewport(
            self,
            ctx: RenderStage,
    ) -> None:
        self._viewport_queue.add(ctx.name)
        self._trigger_dirty()


    # =================================== #
    # Flush Queue
    # =================================== #
    def flush_dirty(self, *_) -> None:

        # ---) LifeCycle
        while self._lifecycle_queue:
            command = self._lifecycle_queue.popleft()

            if command.op == "render":
                assert command.context is not None

                self.sync_render_queue(
                    command.node,
                    command.context,
                )
                self.sync_transform_queue(command.node)
                self.sync_material_queue(command.node)
                self.sync_visibility_queue(command.node)

            elif command.op == "destroy":
                self.sync_destroy_queue(command.node)

        # ---) View
        while self._view_queue:
            name, view = self._view_queue.popitem()
            self.sync_view_queue(view, name)

        # ---) ViewPort
        while self._viewport_queue:
            name = self._viewport_queue.pop()
            self.sync_viewport_queue(name)

        # ---) Transform
        while self._transform_queue:
            node_id = self._transform_queue.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_transform_queue(node)

        # ---) Matrial
        while self._material_queue:
            node_id = self._material_queue.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_material_queue(node)

        # ---) Visiblity
        while self._visibility_queue:
            node_id = self._visibility_queue.pop()
            node = self.instructions.objects.get(node_id)

            if node is not None:
                self.sync_visibility_queue(node)




    # =================================== #
    # Sync
    # =================================== #
    def sync_render_queue(self, node: Node3D, context: str):
        ctx = self.contexts.require_context(context)
        self.instructions.create(node=node, ctx=ctx)

    def sync_destroy_queue(self, node: Node3D):
        self.instructions.destroy(node)

    def sync_transform_queue(
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

    def sync_material_queue(
        self,
        node: Node3D,
    ) -> None:
        for object3d in node.walk(filter="objects"):
            object_id = id(object3d)
            for instructions in self.instructions.by_object.get(object_id, {}).values():
                if not isinstance(instructions, MaterialInstructions):
                    continue

                instructions.set_material(object3d.material)

    def sync_visibility_queue(
        self,
        node: Node3D,
    ) -> None:
        if node.visible_in_tree:
            self.instructions.show(node)
            return

        self.instructions.hide(node)


    def sync_view_queue(
        self,
        view: View,
        name: str,
    ) -> None:

        ctx = self.contexts.require(name)
        ctx.update_view(view)

    def sync_viewport_queue(
        self,
        name: str,
    ) -> None:

        ctx = self.contexts.require(name)
        view = self.views.view_for_context(name)
        if view is None:
            return

        ctx.update_view(view)







