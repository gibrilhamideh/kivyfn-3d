# kivyfn/three/render/instances.py

from __future__ import annotations

from typing import TYPE_CHECKING, overload
from collections import defaultdict

from kivy.event import EventDispatcher

from kivyfn.three.render.context import RenderContext, RenderPass
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
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.types import RenderPassOutput, RenderStage


class RenderInstanceManager(EventDispatcher):
    """
    Manages concrete render instructions.

    A render instruction is:

        Object3D + RenderStage -> BaseInstructions

    This class owns the actual Kivy graphics instructions created for each
    object/stage pair.

    It does NOT decide which objects should render in which stages.
    That belongs to Renderer + render registries.

    Notes:
    - Internal maps are reverse indexes.
    - object3d -> stage_name -> instructions
    - stage_name -> object_id -> instructions
    """

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
        "on_visibility_dirty",
    )

    def __init__(self) -> None:
        super().__init__()

        self._instructions_by_object: defaultdict[int, dict[str, BaseInstructions]] = defaultdict(dict)
        self._instructions_by_stage: defaultdict[str, dict[int, BaseInstructions]] = defaultdict(dict)

        self._objects: dict[int, Object3D] = {}
        self._bound_objects: set[int] = set()

    # =================================== #
    # Lookup
    # =================================== #

    @overload
    def instructions_of(
        self,
        *,
        object3d: Object3D,
        stage_name: None = None,
    ) -> dict[str, BaseInstructions]:
        ...

    @overload
    def instructions_of(
        self,
        *,
        object3d: None = None,
        stage_name: str,
    ) -> dict[int, BaseInstructions]:
        ...

    def instructions_of(
        self,
        *,
        object3d: Object3D | None = None,
        stage_name: str | None = None,
    ) -> dict[str, BaseInstructions] | dict[int, BaseInstructions]:
        if object3d is None and stage_name is None:
            raise ValueError(
                "instructions_of() requires either 'object3d' or 'stage_name'."
            )

        if object3d is not None and stage_name is not None:
            raise ValueError(
                "instructions_of() accepts either 'object3d' or 'stage_name', not both."
            )

        if object3d is not None:
            return self._instructions_by_object.get(id(object3d), {})

        assert stage_name is not None
        return self._instructions_by_stage.get(stage_name, {})

    # =================================== #
    # Create
    # =================================== #

    def create(
        self,
        object3d: Object3D,
        stage: RenderStage,
    ) -> BaseInstructions:
        object_id = id(object3d)
        stage_name = stage.name

        existing = self._instructions_by_object[object_id].get(stage_name)
        if existing is not None:
            return existing

        instructions = self._create_instructions(
            object3d=object3d,
            stage=stage,
        )

        stage.add(instructions.group)

        self._objects[object_id] = object3d
        self._instructions_by_object[object_id][stage_name] = instructions
        self._instructions_by_stage[stage_name][object_id] = instructions

        self.bind_object(object3d)

        return instructions

    def _create_instructions(
        self,
        object3d: Object3D,
        stage: RenderStage,
    ) -> BaseInstructions:
        if isinstance(stage, RenderContext):
            return MaterialInstructions(
                geometry=object3d.geometry,
                material=object3d.material,
                stage=stage,
            )

        return self._create_pass_instructions(
            object3d=object3d,
            stage=stage,
            output=stage.output,
            output_uniform=stage.output_uniform,
        )

    def _create_pass_instructions(
        self,
        object3d: Object3D,
        stage: RenderPass,
        output: RenderPassOutput,
        output_uniform: str,
    ) -> BaseInstructions:
        if output == "depth":
            return DepthInstructions(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "position":
            return PositionInstructions(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "normal":
            return NormalInstructions(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "id":
            return ObjectIdInstructions(
                geometry=object3d.geometry,
                render_id=object3d.require_render_id(),
                stage=stage,
                output_uniform=output_uniform,
            )

        return ColorInstructions(
            geometry=object3d.geometry,
            ctx=stage,
            output_uniform=output_uniform,
        )

    # =================================== #
    # Destroy
    # =================================== #

    def destroy(
        self,
        object3d: Object3D,
        stage: RenderStage | None = None,
    ) -> None:
        if stage is not None:
            self._destroy_instance(
                object3d=object3d,
                stage_name=stage.name,
            )
            return

        for stage_name in list(
            self.instructions_of(
                object3d=object3d,
            )
        ):
            self._destroy_instance(
                object3d=object3d,
                stage_name=stage_name,
            )

    def _destroy_instance(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        object_id = id(object3d)

        stage_map = self._instructions_by_object.get(object_id)
        if stage_map is None:
            return

        instructions = stage_map.pop(stage_name, None)
        if instructions is None:
            return

        instructions.stage.remove(instructions.group)
        instructions.destroy()

        object_map = self._instructions_by_stage.get(stage_name)
        if object_map is not None:
            object_map.pop(object_id, None)

            if not object_map:
                self._instructions_by_stage.pop(stage_name, None)

        if not stage_map:
            self._instructions_by_object.pop(object_id, None)
            self._objects.pop(object_id, None)
            self.unbind_object(object3d)

    # =================================== #
    # Sync
    # =================================== #

    def sync_transform(
        self,
        object3d: Object3D,
    ) -> None:
        model_mat = object3d.world_matrix
        normal_mat = model_mat.compute_normal_matrix()

        for instructions in self.instructions_of(
            object3d=object3d,
        ).values():
            instructions.sync_transform(
                model_mat=model_mat,
                normal_mat=normal_mat,
            )

    def sync_material(
        self,
        object3d: Object3D,
    ) -> None:
        for instructions in self.instructions_of(
            object3d=object3d,
        ).values():
            if isinstance(instructions, MaterialInstructions):
                instructions.set_material(object3d.material)

    def sync_visibility(
        self,
        object3d: Object3D,
    ) -> None:
        for instructions in self.instructions_of(
            object3d=object3d,
        ).values():
            if object3d.visible_in_tree:
                instructions.show()
            else:
                instructions.hide()

    # =================================== #
    # Visibility
    # =================================== #

    def show(
        self,
        object3d: Object3D,
    ) -> None:
        for instructions in self.instructions_of(
            object3d=object3d,
        ).values():
            instructions.show()

    def hide(
        self,
        object3d: Object3D,
    ) -> None:
        for instructions in self.instructions_of(
            object3d=object3d,
        ).values():
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
            on_visibility_dirty=self._on_object_visibility_dirty,
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
            on_visibility_dirty=self._on_object_visibility_dirty,
        )

        self._bound_objects.discard(object_id)

    # =================================== #
    # Dirty Events
    # =================================== #

    def _on_object_transform_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        self.dispatch(
            "on_transform_dirty",
            object3d,
        )

    def _on_object_material_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        self.dispatch(
            "on_material_dirty",
            object3d,
        )

    def _on_object_visibility_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        self.dispatch(
            "on_visibility_dirty",
            object3d,
        )

    def on_transform_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        pass

    def on_material_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        pass

    def on_visibility_dirty(
        self,
        object3d: Object3D,
    ) -> None:
        pass
