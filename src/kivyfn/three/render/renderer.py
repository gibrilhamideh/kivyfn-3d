# kivyfn/three/render/renderer.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup

from kivyfn.three.lights.limits import LightLimits
from kivyfn.three.lights.manager import LightManager
from kivyfn.three.render.instances import RenderInstanceManager
from kivyfn.three.render.registry import (
    RenderMembershipRegistry,
    RenderObjectRegistry,
)
from kivyfn.three.render.stages import RenderStageManager

from kivyfn.three.types import (
    RenderStage,
    SceneObject,
)

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.render.binder import RenderBindingRecord
    from kivyfn.three.render.context import RenderContext, RenderPass2D, RenderPassCube


@dataclass(slots=True)
class RenderCommand:
    op: Literal["render", "remove", "retag"]
    node: SceneObject
    old_tags: set[str] | None = None
    new_tags: set[str] | None = None


class Renderer(EventDispatcher):

    def __init__(
        self,
        scene: Scene,
        canvas: InstructionGroup,
        *,
        max_directional_lights: int,
        max_point_lights: int,
        max_spot_lights: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.scene = scene
        self.canvas = canvas

        self.stages = RenderStageManager()
        self.objects = RenderObjectRegistry()
        self.memberships = RenderMembershipRegistry()
        self.instances = RenderInstanceManager()

        self.lights = LightManager(
            renderer=self,
            limits=LightLimits(
                directional=max_directional_lights,
                point=max_point_lights,
                spot=max_spot_lights,
            ),
        )



        self.instances.bind(
            on_transform_dirty=self.queue_transform,
            on_material_dirty=self.queue_material,
            on_visibility_dirty=self.queue_visibility,
        )

        self.hidden: set[str] = set()

        self._lifecycle_queue: deque[RenderCommand] = deque()
        self._transform_queue: set[int] = set()
        self._material_queue: set[int] = set()
        self._visibility_queue: set[int] = set()

        self._trigger_dirty = Clock.create_trigger(self.flush_dirty, -1)

    def __repr__(self) -> str:
        return (
            "Renderer("
            f"stages={len(self.stages)}, "
            f"objects={len(self.objects)}, "
            ")"
        )

    # =================================== #
    # Contexts
    # =================================== #

    def create_context(
        self,
        **kwargs,
    ) -> RenderContext:

        stage = self.stages.create_context(
            scene=self.scene,
            **kwargs,
        )

        self.canvas.add(stage.ctx)
        self.add_stage_memberships(stage)
        return stage


    def create_pass(
        self,
        **kwargs,
    ) -> RenderPass2D:

        stage = self.stages.create_pass(
            **kwargs,
        )

        self.canvas.add(stage.ctx)
        self.add_stage_memberships(stage)
        return stage

    def create_cube_pass(
        self,
        **kwargs,
    ) -> RenderPassCube:

        stage = self.stages.create_cube_pass(
            **kwargs,
        )

        self.canvas.add(stage.ctx)
        self.add_stage_memberships(stage)
        return stage

    def attach_pass(
        self,
        **kwargs,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        return self.stages.attach_pass(**kwargs)


    # =================================== #
    # Stage Visibility / Destruction
    # =================================== #

    def hide_stage(
        self,
        stage_name: str,
    ) -> None:
        if stage_name in self.hidden:
            return

        stage = self.stages.registry.require(stage_name)
        self.canvas.remove(stage.ctx)
        self.hidden.add(stage_name)

    def show_stage(
        self,
        stage_name: str,
    ) -> None:
        if stage_name not in self.hidden:
            return

        stage = self.stages.registry.require(stage_name)
        self.canvas.add(stage.ctx)
        self.hidden.remove(stage_name)

    def remove_stage(
        self,
        stage_name: str,
    ) -> None:
        stage = self.stages.registry.require(stage_name)
        ctx = self.stages.registry.get_context(stage_name)

        if ctx is not None:
            self.scene.overlays.clear_viewport(ctx.viewport)

        self.remove_stage_memberships(stage)

        if stage.name not in self.hidden:
            self.canvas.remove(stage.ctx)

        self.hidden.discard(stage.name)

        removed = self.stages.remove(stage.name)
        removed.destroy()

    # =================================== #
    # Dirty Queue
    # =================================== #

    def queue_render(
        self,
        node: SceneObject,
    ) -> None:
        self._lifecycle_queue.append(
            RenderCommand(
                op="render",
                node=node,
            )
        )
        self._trigger_dirty()

    def queue_remove(
        self,
        node: SceneObject,
    ) -> None:
        self._lifecycle_queue.append(
            RenderCommand(
                op="remove",
                node=node,
            )
        )
        self._trigger_dirty()

    def queue_retag(
        self,
        node: SceneObject,
        old_tags: set[str],
        new_tags: set[str],
    ) -> None:
        self._lifecycle_queue.append(
            RenderCommand(
                op="retag",
                node=node,
                old_tags=set(old_tags),
                new_tags=set(new_tags),
            )
        )
        self._trigger_dirty()

    def queue_transform(
        self,
        manager: RenderInstanceManager,
        object3d: Object3D,
    ) -> None:
        self._transform_queue.add(id(object3d))
        self._trigger_dirty()

    def queue_material(
        self,
        manager: RenderInstanceManager,
        object3d: Object3D,
    ) -> None:
        self._material_queue.add(id(object3d))
        self._trigger_dirty()

    def queue_visibility(
        self,
        manager: RenderInstanceManager,
        object3d: Object3D,
    ) -> None:
        self._visibility_queue.add(id(object3d))
        self._trigger_dirty()

    # =================================== #
    # Flush Queue
    # =================================== #

    def flush_dirty(
        self,
        *_,
    ) -> None:
        # ---) Lifecycle
        while self._lifecycle_queue:
            command = self._lifecycle_queue.popleft()

            if command.op == "render":
                self.render(command.node)

            elif command.op == "remove":
                self.remove(command.node)

            elif command.op == "retag":
                if command.old_tags is None:
                    raise RuntimeError("Missing old_tags for retag command.")

                if command.new_tags is None:
                    raise RuntimeError("Missing new_tags for retag command.")

                self.retag(
                    command.node,
                    command.old_tags,
                    command.new_tags,
                )

        # ---) Transform
        while self._transform_queue:
            object_id = self._transform_queue.pop()
            object3d = self.objects.get(object_id)

            if object3d is not None:
                self.instances.sync_transform(object3d)

        # ---) Material
        while self._material_queue:
            object_id = self._material_queue.pop()
            object3d = self.objects.get(object_id)

            if object3d is not None:
                self.instances.sync_material(object3d)

        # ---) Visibility
        while self._visibility_queue:
            object_id = self._visibility_queue.pop()
            object3d = self.objects.get(object_id)

            if object3d is not None:
                self.instances.sync_visibility(object3d)

    # =================================== #
    # Lifecycle Sync
    # =================================== #

    def render(
        self,
        node: SceneObject,
    ) -> None:
        self.lights.attach(node)

        for object3d in node.walk(filter="objects"):

            self.objects.register(object3d)
            tags = self.objects.tags_of(object3d)

            desired_stages = self.stages_for_tags(tags)
            current_stages = self.memberships.stages_of(object3d)

            for stage_name in current_stages - desired_stages:
                self.remove_membership(object3d, stage_name)

            for stage_name in desired_stages - current_stages:
                self.add_membership(object3d, stage_name)

            self.instances.sync_transform(object3d)
            self.instances.sync_material(object3d)
            self.instances.sync_visibility(object3d)

    def remove(
        self,
        node: SceneObject,
    ) -> None:
        self.lights.detach(node)

        for object3d in node.walk(filter="objects"):
            active_stages = self.memberships.stages_of(object3d)

            for stage_name in active_stages:
                self.remove_membership(object3d, stage_name)

            self.objects.unregister(object3d)

    def retag(
        self,
        node: SceneObject,
        old_tags: set[str],
        new_tags: set[str],
    ) -> None:
        for object3d in node.walk(filter="objects"):
            if object3d is node:
                self.objects.clear_tags(object3d)

                for tag in new_tags:
                    self.objects.tag(object3d, tag)

                tags = new_tags
            else:
                tags = self.objects.tags_of(object3d)


            current_stages = self.memberships.stages_of(object3d)
            desired_stages = self.stages_for_tags(tags)

            for stage_name in current_stages - desired_stages:
                self.remove_membership(object3d, stage_name)

            for stage_name in desired_stages - current_stages:
                self.add_membership(object3d, stage_name)

            self.instances.sync_transform(object3d)
            self.instances.sync_material(object3d)
            self.instances.sync_visibility(object3d)


    def add_membership(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        stage = self.stages.registry.get(stage_name)
        if stage is None:
            return

        self.instances.create(object3d, stage)
        self.memberships.register(object3d, stage_name)

    def remove_membership(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        stage = self.stages.registry.get(stage_name)
        if stage is not None:
            self.instances.remove(object3d, stage)

        self.memberships.unregister(object3d, stage_name)

    # =================================== #
    # Stage Sync
    # =================================== #

    def add_stage_memberships(
        self,
        stage: RenderStage,
    ) -> None:
        for tag in self.stages.registry.tags_of(stage.name):
            for object3d in self.objects.objects_of(tag):

                tags = self.objects.tags_of(object3d)

                desired_stages = self.stages_for_tags(tags)
                current_stages = self.memberships.stages_of(object3d)

                for stage_name in current_stages - desired_stages:
                    self.remove_membership(object3d, stage_name)

                for stage_name in desired_stages - current_stages:
                    self.add_membership(object3d, stage_name)

                self.instances.sync_transform(object3d)
                self.instances.sync_material(object3d)
                self.instances.sync_visibility(object3d)

    def remove_stage_memberships(
        self,
        stage: RenderStage,
    ) -> None:
        object_ids = self.memberships.memberships_of(stage.name)

        for object_id in object_ids:
            object3d = self.objects.get(object_id)
            if object3d is None:
                continue

            self.instances.remove(object3d, stage)
            self.memberships.unregister(object3d, stage.name)


    # =================================== #
    # Matching
    # =================================== #

    def stages_for_tags(
        self,
        object_tags: set[str],
    ) -> set[str]:
        stage_names: set[str] = set()

        for tag in object_tags:
            for stage in self.stages.registry.stages_of(tag):
                stage_names.add(stage.name)

        return stage_names


