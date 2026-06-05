# kivyfn/three/render/renderer.py

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from dataclasses import dataclass
from collections import deque

from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup

from kivyfn.three.lights.manager import LightManager
from kivyfn.three.views.view_manager import ViewManager
from kivyfn.three.render.stage_manager import RenderStageManager
from kivyfn.three.render.instruction_manager import InstructionManager
from kivyfn.three.render.instructions import MaterialInstructions

from kivyfn.three.types import (
    SceneObject,
    RenderStage,
    RenderContextName,
    RenderPassName,
    RenderStageName,
    ViewName,
)


if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.views.view import View
    from kivyfn.three.render.context import RenderContext, RenderPass
    from kivyfn.three.render.binding_registry import RenderBindingRecord
    from kivyfn.three.render.link_registry import RenderLinkRecord


@dataclass(slots=True)
class RenderCommand:
    op: Literal["render", "destroy"]
    node: SceneObject
    stage_name: str | None = None

class Renderer(EventDispatcher):

    scene_viewport_x = NumericProperty(0)
    scene_viewport_y = NumericProperty(0)
    scene_viewport_width = NumericProperty(100)
    scene_viewport_height = NumericProperty(100)

    def __init__(
        self,
        canvas: InstructionGroup,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.canvas = canvas
        self.stages = RenderStageManager()
        self.instructions = InstructionManager(self.stages)
        self.views = ViewManager()
        self.lights = LightManager(self)

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
            f"stages={len(self.stages)}, "
            f"instructions={len(self.instructions.by_object)}"
            ")"
        )

    # =================================== #
    # Contexts
    # =================================== #
    def create_context(
            self,
            name: RenderContextName,
            view_name: ViewName,
            **kwargs
    ) -> RenderContext:

        view = self.views.require(view_name)

        stage = self.stages.create_context(name=name, **kwargs)
        stage.bind(on_viewport_dirty=self.queue_viewport)

        stage.scene_viewport_x = self.scene_viewport_x
        stage.scene_viewport_y = self.scene_viewport_y
        stage.scene_viewport_width = self.scene_viewport_width
        stage.scene_viewport_height = self.scene_viewport_height

        self.bind(scene_viewport_x=stage.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=stage.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=stage.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=stage.setter("scene_viewport_height"))

        self.views.link(
            view.name,
            stage.name,
        )

        self.canvas.add(stage.ctx)
        return stage


    # =================================== #
    # Render Pass
    # =================================== #
    def create_pass(
            self,
            name: RenderPassName,
            view_name: ViewName,
            **kwargs
    ) -> RenderPass:

        view = self.views.require(view_name)


        stage = self.stages.create_pass(name=name, **kwargs)
        stage.bind(on_viewport_dirty=self.queue_viewport)

        stage.scene_viewport_x = self.scene_viewport_x
        stage.scene_viewport_y = self.scene_viewport_y
        stage.scene_viewport_width = self.scene_viewport_width
        stage.scene_viewport_height = self.scene_viewport_height

        self.bind(scene_viewport_x=stage.setter("scene_viewport_x"))
        self.bind(scene_viewport_y=stage.setter("scene_viewport_y"))
        self.bind(scene_viewport_width=stage.setter("scene_viewport_width"))
        self.bind(scene_viewport_height=stage.setter("scene_viewport_height"))

        self.views.link(
            view.name,
            stage.name,
        )

        self.canvas.add(stage.ctx)
        return stage

    def attach_pass(self, **kwargs) -> RenderBindingRecord | list[RenderBindingRecord]:

        return self.stages.attach_pass(**kwargs)

    # =================================== #
    # Shared
    # =================================== #
    def link_stage(self, **kwargs) -> RenderLinkRecord | list[RenderLinkRecord]:

        return self.stages.link(**kwargs)

    def unlink_stage(self, **kwargs) -> RenderLinkRecord | list[RenderLinkRecord]:

        return self.stages.unlink(**kwargs)

    def hide_stage(
        self,
        name: str,
    ) -> None:

        if name in self.hidden:
            return

        stage = self.stages.require(name)
        self.canvas.remove(stage.ctx)
        self.hidden.add(name)

    def show_stage(
        self,
        name: str,
    ) -> None:

        if name not in self.hidden:
            return

        stage = self.stages.require(name)
        self.canvas.add(stage.ctx)
        self.hidden.remove(name)

    def destroy_stage(
        self,
        name: str,
    ) -> None:

        if name not in self.hidden:
            stage = self.stages.require(name)
            self.canvas.remove(stage.ctx)

        self.stages.destroy(name)

    # =================================== #
    # Dirty Queue
    # =================================== #
    def queue_render(
        self,
        node: SceneObject,
        *,
        stage: RenderStageName | None = None,
        stages: list[RenderStageName] | None = None,
    ) -> None:

        stage_names = [stage] if stage is not None else stages

        if stage_names is None:
            raise RuntimeError("Unexpected missing render stages.")

        for stage_name in stage_names:
            self._lifecycle_queue.append(
                RenderCommand(
                    op="render",
                    node=node,
                    stage_name=stage_name,
                )
            )

        self._trigger_dirty()


    def queue_destroy(
        self,
        node: SceneObject,
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
        manager: InstructionManager,
        node: SceneObject,
    ) -> None:
        self._transform_queue.add(id(node))
        self._trigger_dirty()

    def queue_material(
        self,
        manager: InstructionManager,
        node: SceneObject,
    ) -> None:
        self._material_queue.add(id(node))
        self._trigger_dirty()

    def queue_visibility(
        self,
        manager: InstructionManager,
        node: SceneObject,
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
            stage: RenderStage,
    ) -> None:
        self._viewport_queue.add(stage.name)
        self._trigger_dirty()



    # =================================== #
    # Flush Queue
    # =================================== #
    def flush_dirty(self, *_) -> None:

        # ---) LifeCycle
        while self._lifecycle_queue:
            command = self._lifecycle_queue.popleft()

            if command.op == "render":
                assert command.stage_name is not None

                self.sync_render_queue(
                    command.node,
                    command.stage_name,
                )
                self.sync_transform_queue(command.node)
                self.sync_material_queue(command.node)
                self.sync_visibility_queue(command.node)

                self.lights.create(command.node)

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
    def sync_render_queue(self, node: SceneObject, stage_name: str):
        stage = self.stages.require_context(stage_name)
        self.instructions.create(node=node, stage=stage)

    def sync_destroy_queue(self, node: Node3D):
        self.instructions.destroy(node)

    def sync_transform_queue(
        self,
        node: SceneObject,
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
        node: SceneObject,
    ) -> None:
        for object3d in node.walk(filter="objects"):
            object_id = id(object3d)
            for instructions in self.instructions.by_object.get(object_id, {}).values():
                if not isinstance(instructions, MaterialInstructions):
                    continue

                instructions.set_material(object3d.material)

    def sync_visibility_queue(
        self,
        node: SceneObject,
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

        stage = self.stages.require(name)
        stage.update_view(view)

    def sync_viewport_queue(
        self,
        name: str,
    ) -> None:

        stage = self.stages.require(name)
        view = self.views.view_for_stage(name)
        if view is None:
            return

        stage.update_view(view)


