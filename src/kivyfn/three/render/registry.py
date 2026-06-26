
# kivyfn/three/render/stage_registry.py
from __future__ import annotations

from collections import defaultdict
from typing import NoReturn

from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.render.stage import RenderStage


class RenderStageRegistry:
    """
    Tracks render stages and their render tags.

    Responsibilities:
    - Register and unregister RenderStage instances.
    - Support direct lookup by stage name.
    - Maintain stage -> tags relationships.
    - Maintain tag -> stage relationships.
    - Support lookup of stages by one render tag.

    This registry does NOT track scene objects.
    This registry does NOT track active object membership in stages.

    Notes:
    - All tag operations are scalar.
    - This registry does not compute multi-tag matches.
    - Callers that need multi-tag logic should loop outside the registry.
    """

    def __init__(
        self,
    ) -> None:
        self._stages: dict[str, RenderStage] = {}

        self._stage_tags: dict[str, set[str]] = {}
        self._tag_stages: dict[str, set[str]] = defaultdict(set)

    def __len__(
        self,
    ) -> int:
        return len(self._stages)

    @property
    def stages(
        self,
    ) -> dict[str, RenderStage]:
        return self._stages.copy()

    @property
    def screen_stages(
        self,
    ) -> dict[str, RenderStage]:
        return {
            name: stage
            for name, stage in self._stages.items()
            if stage.is_screen
        }

    @property
    def texture_2d_stages(
        self,
    ) -> dict[str, RenderStage]:
        return {
            name: stage
            for name, stage in self._stages.items()
            if stage.is_texture_2d
        }

    @property
    def texture_cube_stages(
        self,
    ) -> dict[str, RenderStage]:
        return {
            name: stage
            for name, stage in self._stages.items()
            if stage.is_texture_cube
        }

    @property
    def output_stages(
        self,
    ) -> dict[str, RenderStage]:
        return {
            name: stage
            for name, stage in self._stages.items()
            if stage.is_texture_2d or stage.is_texture_cube
        }

    # =================================== #
    # Stages
    # =================================== #

    def register(
        self,
        stage: RenderStage,
    ) -> None:
        stage_name = stage.name

        if stage_name in self._stages:
            raise ValueError(
                f"Render stage {stage_name!r} is already registered."
            )

        self._stages[stage_name] = stage

    def unregister(
        self,
        stage_name: str,
    ) -> RenderStage:
        stage = self.require(stage_name)

        self.clear_tags(stage_name)
        del self._stages[stage_name]

        return stage

    def exists(
        self,
        stage_name: str,
    ) -> bool:
        return stage_name in self._stages

    # =================================== #
    # Get
    # =================================== #

    def get(
        self,
        stage_name: str,
    ) -> RenderStage | None:
        return self._stages.get(stage_name)

    def get_screen_stage(
        self,
        stage_name: str,
    ) -> RenderStage | None:
        stage = self.get(stage_name)

        if stage is None or not stage.is_screen:
            return None

        return stage

    def get_texture_2d_stage(
        self,
        stage_name: str,
    ) -> RenderStage | None:
        stage = self.get(stage_name)

        if stage is None or not stage.is_texture_2d:
            return None

        return stage

    def get_texture_cube_stage(
        self,
        stage_name: str,
    ) -> RenderStage | None:
        stage = self.get(stage_name)

        if stage is None or not stage.is_texture_cube:
            return None

        return stage

    def get_output_stage(
        self,
        stage_name: str,
    ) -> RenderStage | None:
        stage = self.get(stage_name)

        if stage is None:
            return None

        if not stage.is_texture_2d and not stage.is_texture_cube:
            return None

        return stage

    # =================================== #
    # Require
    # =================================== #

    def require(
        self,
        stage_name: str,
    ) -> RenderStage | NoReturn:
        stage = self.get(stage_name)

        if stage is None:
            raise KeyError(
                f"Render stage {stage_name!r} is not registered."
            )

        return stage

    def require_screen_stage(
        self,
        stage_name: str,
    ) -> RenderStage:
        stage = self.require(stage_name)

        if not stage.is_screen:
            raise TypeError(
                f"Render stage {stage_name!r} is not a screen stage."
            )

        return stage

    def require_texture_2d_stage(
        self,
        stage_name: str,
    ) -> RenderStage:
        stage = self.require(stage_name)

        if not stage.is_texture_2d:
            raise TypeError(
                f"Render stage {stage_name!r} is not a texture-2d stage."
            )

        return stage

    def require_texture_cube_stage(
        self,
        stage_name: str,
    ) -> RenderStage:
        stage = self.require(stage_name)

        if not stage.is_texture_cube:
            raise TypeError(
                f"Render stage {stage_name!r} is not a texture-cube stage."
            )

        return stage

    def require_output_stage(
        self,
        stage_name: str,
    ) -> RenderStage:
        stage = self.require(stage_name)

        if not stage.is_texture_2d and not stage.is_texture_cube:
            raise TypeError(
                f"Render stage {stage_name!r} is not an output stage."
            )

        return stage

    # =================================== #
    # Tags
    # =================================== #

    def tag(
        self,
        stage_name: str,
        tag: str,
    ) -> None:
        self.require(stage_name)

        self._stage_tags.setdefault(stage_name, set()).add(tag)
        self._tag_stages[tag].add(stage_name)

    def untag(
        self,
        stage_name: str,
        tag: str,
    ) -> None:
        stage_tags = self._stage_tags.get(stage_name)
        if stage_tags is not None:
            stage_tags.discard(tag)

            if not stage_tags:
                self._stage_tags.pop(stage_name, None)

        stage_names = self._tag_stages.get(tag)
        if stage_names is not None:
            stage_names.discard(stage_name)

            if not stage_names:
                self._tag_stages.pop(tag, None)

    def clear_tags(
        self,
        stage_name: str,
    ) -> set[str]:
        self.require(stage_name)

        old_tags = self.tags_of(stage_name)

        for tag in old_tags:
            self.untag(stage_name, tag)

        return old_tags

    def tags_of(
        self,
        stage_name: str,
    ) -> set[str]:
        self.require(stage_name)

        return set(self._stage_tags.get(stage_name, set()))

    # =================================== #
    # Selection
    # =================================== #

    def stages_of(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return [
            stage
            for stage_name in self._tag_stages.get(tag, set())
            if (stage := self.get(stage_name)) is not None
        ]

    def screen_stages_of(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return [
            stage
            for stage in self.stages_of(tag)
            if stage.is_screen
        ]

    def texture_2d_stages_of(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return [
            stage
            for stage in self.stages_of(tag)
            if stage.is_texture_2d
        ]

    def texture_cube_stages_of(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return [
            stage
            for stage in self.stages_of(tag)
            if stage.is_texture_cube
        ]

    def output_stages_of(
        self,
        tag: str,
    ) -> list[RenderStage]:
        return [
            stage
            for stage in self.stages_of(tag)
            if stage.is_texture_2d or stage.is_texture_cube
        ]



class RenderMembershipRegistry:
    """
    Tracks active render membership.

    Responsibilities:
    - Record which objects are currently rendered in which stages.
    - Record which stages currently contain which objects.
    - Support efficient stage add/remove diffs during retagging.

    Examples:

        object_id 123
            -> {"main", "id-pass"}

        stage "main"
            -> {123, 456, 789}

    Membership represents actual renderer state.

    If an object appears here, instructions have been created
    for the corresponding render stage.
    """
    def __init__(self) -> None:
        self._by_object: dict[int, set[str]] = {}
        self._by_stage: dict[str, set[int]] = {}

    def stages_of(self, object3d: Object3D) -> set[str]:
        return set(self._by_object.get(id(object3d), set()))

    def memberships_of(self, stage_name: str) -> set[int]:
        return set(self._by_stage.get(stage_name, set()))

    def register(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        object_id = id(object3d)

        self._by_object.setdefault(object_id, set()).add(stage_name)
        self._by_stage.setdefault(stage_name, set()).add(object_id)

    def unregister(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        object_id = id(object3d)

        stages = self._by_object.get(object_id)
        if stages is not None:
            stages.discard(stage_name)
            if not stages:
                self._by_object.pop(object_id, None)

        objects = self._by_stage.get(stage_name)
        if objects is not None:
            objects.discard(object_id)
            if not objects:
                self._by_stage.pop(stage_name, None)

    def clear(self, object3d: Object3D) -> set[str]:
        old_stages = self.stages_of(object3d)

        for stage_name in old_stages:
            self.unregister(object3d, stage_name)

        return old_stages



class RenderObjectRegistry:
    """
    Tracks renderable objects and their render tags.

    Responsibilities:
    - Register Object3D instances participating in rendering.
    - Maintain object -> tags relationships.
    - Maintain tag -> object relationships.
    - Support lookup by object id.
    - Support lookup of objects by one render tag.

    This registry describes what an object wants to participate in.
    RenderMembershipRegistry describes where an object is currently rendered.

    Notes:
    - All tag operations are scalar.
    - This registry does not compute multi-tag matches.
    - Callers that need multi-tag logic should loop outside the registry.
    """

    def __init__(self) -> None:
        self._objects: dict[int, Object3D] = {}
        self._object_tags: dict[int, set[str]] = {}
        self._tag_objects: dict[str, set[int]] = defaultdict(set)

    def __len__(self) -> int:
        return len(self._objects)

    # =================================== #
    # Objects
    # =================================== #

    def get(
        self,
        object_id: int,
    ) -> Object3D | None:
        return self._objects.get(object_id)

    def register(
        self,
        object3d: Object3D,
    ) -> None:
        object_id = id(object3d)
        tags = object3d.tags

        self._objects[object_id] = object3d
        self.clear_tags(object3d)

        for tag in tags:
            self.tag(object3d, tag)

    def unregister(
        self,
        object3d: Object3D,
    ) -> None:
        self.clear_tags(object3d)
        self._objects.pop(id(object3d), None)

    # =================================== #
    # Tags
    # =================================== #

    def tag(
        self,
        object3d: Object3D,
        tag: str,
    ) -> None:
        object_id = id(object3d)

        self._objects[object_id] = object3d
        self._object_tags.setdefault(object_id, set()).add(tag)
        self._tag_objects[tag].add(object_id)

    def untag(
        self,
        object3d: Object3D,
        tag: str,
    ) -> None:
        object_id = id(object3d)

        tags = self._object_tags.get(object_id)
        if tags is not None:
            tags.discard(tag)

            if not tags:
                self._object_tags.pop(object_id, None)

        object_ids = self._tag_objects.get(tag)
        if object_ids is not None:
            object_ids.discard(object_id)

            if not object_ids:
                self._tag_objects.pop(tag, None)

    def clear_tags(
        self,
        object3d: Object3D,
    ) -> set[str]:
        old_tags = self.tags_of(object3d)

        for tag in old_tags:
            self.untag(object3d, tag)

        return old_tags

    def tags_of(
        self,
        object3d: Object3D,
    ) -> set[str]:
        return set(self._object_tags.get(id(object3d), set()))

    # =================================== #
    # Selection
    # =================================== #

    def objects_of(
        self,
        tag: str,
    ) -> list[Object3D]:
        return [
            object3d
            for object_id in self._tag_objects.get(tag, set())
            if (object3d := self._objects.get(object_id)) is not None
        ]




