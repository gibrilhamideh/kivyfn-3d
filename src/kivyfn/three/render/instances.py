# kivyfn/three/render/instances.py

from __future__ import annotations

from typing import overload
from collections import defaultdict

from kivy.event import EventDispatcher
from kivy.graphics import (
    InstructionGroup,
    Mesh,
)

from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.assets.deformation import Deformation
from kivyfn.three.graphics.gl.context import (
    BindGeometry,
    BindMaterial,
    BindObjectId,
    BindTexture,
    BindTransform,
    BindDeformation,
)
from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.render.config import TEXTURE_SLOTS
from kivyfn.three.render.stage import RenderStage


class RenderInstanceManager():
    """
    Owns render instances for object/stage pairs.

    A render instance is:

        Object3D + RenderStage -> RenderInstance

    Each instance owns the concrete Kivy graphics instruction group needed
    to render one object in one stage.

    This manager does NOT decide which objects belong to which stages.
    That belongs to Renderer and the render registries.
    """


    def __init__(
        self,
    ) -> None:
        super().__init__()

        self._instances_by_object: defaultdict[int, dict[str, RenderInstance]] = (
            defaultdict(dict)
        )
        self._instances_by_stage: defaultdict[str, dict[int, RenderInstance]] = (
            defaultdict(dict)
        )

        self._objects: dict[int, Object3D] = {}
        self._bound_objects: set[int] = set()

    # =================================== #
    # Lookup
    # =================================== #

    @overload
    def instances_of(
        self,
        *,
        object3d: Object3D,
        stage_name: None = None,
    ) -> dict[str, RenderInstance]:
        ...

    @overload
    def instances_of(
        self,
        *,
        object3d: None = None,
        stage_name: str,
    ) -> dict[int, RenderInstance]:
        ...

    def instances_of(
        self,
        *,
        object3d: Object3D | None = None,
        stage_name: str | None = None,
    ) -> dict[str, RenderInstance] | dict[int, RenderInstance]:
        if object3d is None and stage_name is None:
            raise ValueError(
                "instances_of() requires either 'object3d' or 'stage_name'."
            )

        if object3d is not None and stage_name is not None:
            raise ValueError(
                "instances_of() accepts either 'object3d' or 'stage_name', "
                "not both."
            )

        if object3d is not None:
            return self._instances_by_object.get(id(object3d), {})

        assert stage_name is not None

        return self._instances_by_stage.get(stage_name, {})

    # =================================== #
    # Create
    # =================================== #

    def create(
        self,
        object3d: Object3D,
        stage: RenderStage,
    ) -> RenderInstance:
        object_id = id(object3d)
        stage_name = stage.name

        existing = self._instances_by_object[object_id].get(stage_name)
        if existing is not None:
            return existing

        instance = RenderInstance(
            geometry=object3d.geometry,
            material=object3d.material,
            deformation=object3d.deformation,
            render_id=object3d.require_render_id()
            if stage.use_render_id
            else None,
            stage=stage,
        )

        stage.add(instance.group)

        self._objects[object_id] = object3d
        self._instances_by_object[object_id][stage_name] = instance
        self._instances_by_stage[stage_name][object_id] = instance

        return instance

    # =================================== #
    # Remove
    # =================================== #

    def remove(
        self,
        object3d: Object3D,
        stage: RenderStage | None = None,
    ) -> None:
        if stage is not None:
            self._remove_instance(
                object3d=object3d,
                stage_name=stage.name,
            )
            return

        for stage_name in list(
            self.instances_of(
                object3d=object3d,
            )
        ):
            self._remove_instance(
                object3d=object3d,
                stage_name=stage_name,
            )

    def _remove_instance(
        self,
        object3d: Object3D,
        stage_name: str,
    ) -> None:
        object_id = id(object3d)

        stage_map = self._instances_by_object.get(object_id)
        if stage_map is None:
            return

        instance = stage_map.pop(stage_name, None)
        if instance is None:
            return

        instance.stage.remove(instance.group)
        instance.destroy()

        object_map = self._instances_by_stage.get(stage_name)
        if object_map is not None:
            object_map.pop(object_id, None)

            if not object_map:
                self._instances_by_stage.pop(stage_name, None)

        if not stage_map:
            self._instances_by_object.pop(object_id, None)
            self._objects.pop(object_id, None)

    # =================================== #
    # Sync
    # =================================== #

    def sync_transform(
        self,
        object3d: Object3D,
    ) -> None:
        model_mat = object3d.world_matrix
        normal_mat = model_mat.to_normal()

        for instance in self.instances_of(object3d=object3d).values():
            instance.sync_transform(
                model_mat=model_mat,
                normal_mat=normal_mat,
            )

    def sync_material(
        self,
        object3d: Object3D,
    ) -> None:
        for instance in self.instances_of(object3d=object3d).values():
            instance.set_material(object3d.material)

    def sync_visibility(
        self,
        object3d: Object3D,
    ) -> None:
        for instance in self.instances_of(object3d=object3d).values():
            if object3d.visible_in_tree:
                instance.show()
            else:
                instance.hide()


    def sync_deformation(
        self,
        object3d: Object3D,
    ) -> None:
        for instance in self.instances_of(object3d=object3d).values():
            instance.sync_deformation(
                deformation=object3d.deformation,
            )

    # =================================== #
    # Visibility
    # =================================== #

    def show(
        self,
        object3d: Object3D,
    ) -> None:
        for instance in self.instances_of(object3d=object3d).values():
            instance.show()

    def hide(
        self,
        object3d: Object3D,
    ) -> None:
        for instance in self.instances_of(object3d=object3d).values():
            instance.hide()


class RenderInstance(EventDispatcher):
    def __init__(
        self,
        *,
        geometry: Geometry,
        material: Material,
        deformation: Deformation,
        render_id: int | None,
        stage: RenderStage,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.stage = stage
        self.geometry = geometry
        self.material = material
        self.render_id = render_id
        self.visible = True

        self.group = InstructionGroup()

        self.texture_group = InstructionGroup()
        self.texture_binders: dict[str, BindTexture] = {}

        self.bind_transform = BindTransform()

        self.bind_geometry = BindGeometry(
            use_tangents=geometry.has_tangents,
            use_skinning=geometry.has_skin,
            use_colors=geometry.has_colors
        )

        self.bind_deformation = BindDeformation(
            deformation=deformation,
        )

        self.bind_material = BindMaterial(
            material=material,
        )

        self.bind_object_id: BindObjectId | None = None

        if stage.use_render_id:
            if render_id is None:
                raise ValueError(
                    f"Render stage {stage.name!r} requires render_id."
                )

            target = stage.require_target(
                "render-pass",
            )

            self.bind_object_id = BindObjectId(
                render_id=render_id,
                uniform=target.attach_as,
            )

        self.mesh = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.fmt,
            mode=geometry.mode,
        )

        self.instructions = []

        self.sync_textures(
            rebuild=False,
        )
        self.sync_uniforms()
        self.rebuild()

    # =================================== #
    # Build
    # =================================== #

    def build_instructions(
        self,
    ) -> list:
        instructions = [
            self.bind_transform,
            self.bind_geometry,
            self.bind_deformation,
        ]

        if self.stage.use_material:
            instructions.append(
                self.bind_material,
            )

        if self.bind_object_id is not None:
            instructions.append(
                self.bind_object_id,
            )

        if self.stage.use_textures:
            instructions.append(
                self.texture_group,
            )

        instructions.append(
            self.mesh,
        )

        return instructions

    def rebuild(
        self,
    ) -> None:
        self.group.clear()
        self.instructions.clear()

        if not self.visible:
            return

        self.instructions.extend(
            self.build_instructions(),
        )

        for instruction in self.instructions:
            if instruction is not None:
                self.group.add(
                    instruction,
                )

    # =================================== #
    # Sync
    # =================================== #
    def sync_deformation(
        self,
        *,
        deformation: Deformation,
    ) -> None:
        self.bind_deformation.sync(
            deformation=deformation,
        )

    def sync_transform(
        self,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.bind_transform.sync(
            model_mat=model_mat,
            normal_mat=normal_mat,
        )

    def sync_uniforms(
        self,
        *_,
    ) -> None:
        if self.stage.use_material:
            self.bind_material.sync(
                material=self.material,
            )

        if self.bind_object_id is not None:
            self.bind_object_id.sync()

    def sync_textures(
        self,
        *_,
        rebuild: bool = True,
    ) -> None:
        _ = rebuild

        if not self.stage.use_textures:
            self.clear_texture_binders(
                rebuild=False,
            )
            return

        textures = self.material.textures

        for name, slot in TEXTURE_SLOTS.items():
            texture = textures.get(
                name,
            )

            binder = self.texture_binders.get(
                name,
            )

            if texture is None:
                if binder is not None:
                    self.texture_binders.pop(
                        name,
                    )

                    self.texture_group.remove(
                        binder,
                    )

                continue

            if binder is None:
                binder = BindTexture(
                    uniform=name,
                    texture=texture,
                    slot=slot,
                )

                self.texture_binders[name] = binder

                self.texture_group.add(
                    binder,
                )

                continue

            if binder.texture is not texture or binder.slot != slot:
                binder.sync(
                    texture=texture,
                    slot=slot,
                )

        if self.stage.use_material:
            self.bind_material.sync(
                material=self.material,
            )

    def clear_texture_binders(
        self,
        *,
        rebuild: bool = True,
    ) -> None:
        _ = rebuild

        if not self.texture_binders:
            return

        self.texture_binders.clear()
        self.texture_group.clear()

    def set_material(
        self,
        material: Material,
    ) -> None:
        self.material = material

        self.bind_material.set_material(
            material,
        )

        self.sync_uniforms()
        self.sync_textures()

    # =================================== #
    # Visibility
    # =================================== #

    def show(
        self,
    ) -> None:
        if self.visible:
            return

        self.visible = True
        self.rebuild()

    def hide(
        self,
    ) -> None:
        if not self.visible:
            return

        self.visible = False
        self.rebuild()

    # =================================== #
    # Delete
    # =================================== #

    def destroy(
        self,
    ) -> None:
        self.clear_texture_binders(
            rebuild=False,
        )
        self.instructions.clear()
        self.group.clear()

