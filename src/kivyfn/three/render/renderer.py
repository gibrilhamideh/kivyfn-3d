# kivyfn/three/render/renderer.py

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.graphics import InstructionGroup

from kivyfn.three.types import SceneObject
from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.lights.limits import LightLimits
from kivyfn.three.lights.manager import LightManager
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.render.instances import RenderInstanceManager
from kivyfn.three.render.stages import RenderStageManager
from kivyfn.three.render.registry import (
    RenderMembershipRegistry,
    RenderObjectRegistry,
)

from kivyfn.three.utils.stopwatch import Stopwatch


if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.render.binder import RenderBindingRecord
    from kivyfn.three.render.stage import RenderStage


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


        self.hidden: set[str] = set()

        self._lifecycle_queue: deque[RenderCommand] = deque()
        self._transform_queue: set[int] = set()
        self._material_queue: set[int] = set()
        self._visibility_queue: set[int] = set()
        self._deformation_queue: set[int] = set()

        self._flush_scheduled = False
        self._trigger_dirty = Clock.create_trigger(self.flush, -1)

        self.profile_flush = True
        self.profile_flush_every = 60
        self._profile_flush_count = 0

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

    def create_screen_stage(
        self,
        **kwargs,
    ) -> RenderStage:
        stage = self.stages.create_screen_stage(
            scene=self.scene,
            **kwargs,
        )

        self.canvas.add(stage.target)
        self.add_stage_memberships(stage)

        return stage

    def create_texture_2d_stage(
        self,
        **kwargs,
    ) -> RenderStage:
        stage = self.stages.create_texture_2d_stage(
            scene=self.scene,
            **kwargs,
        )

        self.canvas.add(stage.target)
        self.add_stage_memberships(stage)

        return stage

    def create_texture_cube_stage(
        self,
        **kwargs,
    ) -> RenderStage:
        stage = self.stages.create_texture_cube_stage(
            scene=self.scene,
            **kwargs,
        )

        self.canvas.add(stage.target)
        self.add_stage_memberships(stage)

        return stage

    def attach_output(
        self,
        **kwargs,
    ) -> RenderBindingRecord | list[RenderBindingRecord]:
        return self.stages.attach_output(**kwargs)


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

        self.canvas.remove(stage.target)
        self.hidden.add(stage_name)

    def show_stage(
        self,
        stage_name: str,
    ) -> None:
        if stage_name not in self.hidden:
            return

        stage = self.stages.registry.require(stage_name)

        self.canvas.add(stage.target)
        self.hidden.remove(stage_name)

    def remove_stage(
        self,
        stage_name: str,
    ) -> None:
        stage = self.stages.registry.require(stage_name)

        self.scene.overlays.clear_stage(stage.name)

        self.remove_stage_memberships(stage)

        if stage.name not in self.hidden:
            self.canvas.remove(stage.target)

        self.hidden.discard(stage.name)

        removed = self.stages.remove(stage.name)
        removed.delete()

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
        self._wake()

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
        self._wake()

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
        self._wake()

    def queue_transform(
        self,
        node: SceneObject,
    ) -> None:
        self._transform_queue.add(id(node))
        self._wake()

    def queue_deformation(
        self,
        object3d: Object3D,
    ) -> None:
        self._deformation_queue.add(id(object3d))
        self._wake()

    def queue_material(
        self,
        object3d: Object3D,
    ) -> None:
        self._material_queue.add(id(object3d))
        self._wake()

    def queue_visibility(
        self,
        node: SceneObject,
    ) -> None:
        self._visibility_queue.add(id(node))
        self._wake()

    # =================================== #
    # Flush Queue
    # =================================== #
    def flush(
        self,
        *_,
    ) -> None:
        self._flush_scheduled = False

        if not self.profile_flush:
            self.flush_lifecycle()
            self.flush_transform()
            self.flush_material()
            self.flush_deformation()
            self.flush_visibility()
            return

        self._profile_flush_count += 1

        Stopwatch.add_count(
            "queue.lifecycle",
            len(self._lifecycle_queue),
        )
        Stopwatch.add_count(
            "queue.transform",
            len(self._transform_queue),
        )
        Stopwatch.add_count(
            "queue.material",
            len(self._material_queue),
        )
        Stopwatch.add_count(
            "queue.deformation",
            len(self._deformation_queue),
        )
        Stopwatch.add_count(
            "queue.visibility",
            len(self._visibility_queue),
        )

        with Stopwatch.section("flush.total"):
            with Stopwatch.section("flush.lifecycle"):
                self.flush_lifecycle()

            with Stopwatch.section("flush.transform"):
                self.flush_transform()

            with Stopwatch.section("flush.material"):
                self.flush_material()

            with Stopwatch.section("flush.deformation"):
                self.flush_deformation()

            with Stopwatch.section("flush.visibility"):
                self.flush_visibility()

        if self._profile_flush_count % self.profile_flush_every == 0:
            Stopwatch.summary(
                clear=True,
                min_ms=0.01,
            )

    def flush_lifecycle(
        self,
    ) -> None:
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

    def flush_transform(
        self,
    ) -> None:
        dirty_ids = self._transform_queue

        if not dirty_ids:
            return

        self._transform_queue = set()

        registry = self.scene.registry
        instances = self.instances
        objects = self.objects
        deformation_queue = self._deformation_queue

        affected_ids = registry.affected_by_compressed_tree(
            dirty_ids,
            ids=True,
        )

        dirty_joint_ids: set[int] = set()
        dirty_object_ids: set[int] = set()

        by_id = registry.by_id
        object_ids = registry.object_ids
        is_joint_id = registry.is_joint_id
        sync_matrix = self.sync_matrix

        for affected_id in affected_ids:
            node = by_id.get(
                affected_id,
            )

            if node is None:
                continue

            if affected_id not in dirty_ids:
                node._world_matrix_dirty = True

            sync_matrix(
                node,
            )

            if is_joint_id(
                affected_id,
            ):
                dirty_joint_ids.add(
                    affected_id,
                )

            if affected_id in object_ids:
                dirty_object_ids.add(
                    affected_id,
                )

        for object_id in dirty_object_ids:
            object3d = objects.get(
                object_id,
            )

            if object3d is None:
                continue

            instances.sync_transform(
                object3d,
            )

            if object3d.skin is not None:
                deformation_queue.add(
                    object_id,
                )

        if dirty_joint_ids:
            deformation_queue.update(
                registry.affected_by_joints(
                    dirty_joint_ids,
                    ids=True,
                )
            )

    def flush_material(
        self,
    ) -> None:
        dirty_ids = self._material_queue

        if not dirty_ids:
            return

        self._material_queue = set()

        objects = self.objects
        instances = self.instances

        for object_id in dirty_ids:
            object3d = objects.get(object_id)

            if object3d is None:
                continue

            instances.sync_material(object3d)

    def flush_deformation(
        self,
    ) -> None:
        dirty_ids = self._deformation_queue

        if not dirty_ids:
            return

        self._deformation_queue = set()

        objects = self.objects
        instances = self.instances

        for object_id in dirty_ids:
            object3d = objects.get(object_id)

            if object3d is None:
                continue

            if object3d.skin is None:
                continue

            self.sync_deformation(object3d)
            instances.sync_deformation(object3d)

    def flush_visibility(
        self,
    ) -> None:
        dirty_ids = self._visibility_queue

        if not dirty_ids:
            return

        self._visibility_queue = set()

        registry = self.scene.registry
        instances = self.instances
        objects = self.objects

        visible_ids = registry.affected_by_compressed_tree(
            dirty_ids,
            ids=True,
        )

        for node_id in visible_ids:
            object3d = registry.object_by_id(
                node_id,
            )

            if object3d is None:
                continue

            if objects.get(id(object3d)) is None:
                continue

            instances.sync_visibility(object3d)

    # =================================== #
    # Lifecycle Sync
    # =================================== #
    def render(
        self,
        node: SceneObject,
    ) -> None:
        self.lights.attach(node)

        for affected in self.scene.registry.affected_by_tree(
            node,
        ):
            self.sync_matrix(affected)

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
            self.instances.sync_deformation(object3d)
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
            self.instances.sync_deformation(object3d)
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
                self.instances.sync_deformation(object3d)
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

    # =================================== #
    # Matching
    # =================================== #
    def sync_matrix(
        self,
        node: SceneObject,
    ) -> None:
        if node._local_matrix_dirty:
            origin = node.origin

            if origin.is_zero():
                node._local_matrix.set_from(
                    node.transform.matrix,
                )
            else:
                node.transform.write_matrix4(
                    node._local_matrix,
                    origin=origin,
                )

            node._local_matrix_dirty = False

        if not node._world_matrix_dirty:
            return

        parent = node.parent

        if parent is None:
            node._world_matrix.set_from(
                node._local_matrix,
            )
        else:
            node._world_matrix.multiply_from(
                parent._world_matrix,
                node._local_matrix,
            )

        node._world_matrix_dirty = False

    def sync_deformation(
        self,
        object3d: Object3D,
    ) -> None:
        object3d.deformation.sync_joint_matrices_for(
            object3d,
        )

    # =================================== #
    # Helpers
    # =================================== #
    def _wake(self) -> None:
        if self._flush_scheduled:
            return

        self._flush_scheduled = True
        self._trigger_dirty()
