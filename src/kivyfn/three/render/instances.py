# kivyfn/three/render/instances.py

from __future__ import annotations

from collections import defaultdict
from typing import overload

from kivy.event import EventDispatcher
from kivy.graphics import (
    InstructionGroup,
    Mesh,
)
from kivyfn.three.assets.geometry import Geometry
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.graphics.gl.bind import BindTexture
from kivyfn.three.render.stage import RenderStage
from kivyfn.three.render.config import TEXTURE_SLOTS
from kivyfn.three.render.callbacks import (
    MaterialCallback,
    ObjectIdCallback,
    TransformCallback,
    GeometryCallback,
)


class RenderInstanceManager(EventDispatcher):
    """
    Owns render instances for object/stage pairs.

    A render instance is:

        Object3D + RenderStage -> RenderInstance

    Each instance owns the concrete Kivy graphics instruction group needed
    to render one object in one stage.

    This manager does NOT decide which objects belong to which stages.
    That belongs to Renderer and the render registries.
    """

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
        "on_visibility_dirty",
    )

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
            render_id=object3d.require_render_id()
            if stage.use_render_id
            else None,
            stage=stage,
        )

        stage.add(instance.group)

        self._objects[object_id] = object3d
        self._instances_by_object[object_id][stage_name] = instance
        self._instances_by_stage[stage_name][object_id] = instance

        self.bind_object(object3d)

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


class RenderInstance(EventDispatcher):
    def __init__(
        self,
        *,
        geometry: Geometry,
        material: Material,
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
        self.render_group = InstructionGroup()

        self.texture_binders: dict[str, BindTexture] = {}

        self.transform_callback = TransformCallback(
            stage=stage,
        )

        self.geometry_callback = GeometryCallback(
            stage=stage,
            has_tangents=geometry.has_tangents,
        )

        self.material_callback = MaterialCallback(
            stage=stage,
            material=material,
        )

        self.object_id_callback: ObjectIdCallback | None = None

        if stage.use_render_id:
            if render_id is None:
                raise ValueError(
                    f"Render stage {stage.name!r} requires render_id."
                )

            target = stage.require_target("render-pass")

            self.object_id_callback = ObjectIdCallback(
                stage=stage,
                render_id=render_id,
                uniform=target.attach_as,
            )

        self.mesh = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.fmt,
            mode=geometry.mode,
            texture=geometry.texture,
        )

        self.rebuild()
        self.sync_uniforms()
        self.sync_textures()

    # =================================== #
    # Build
    # =================================== #

    def rebuild(
        self,
    ) -> None:
        self.group.clear()
        self.texture_group.clear()
        self.render_group.clear()

        if not self.visible:
            return

        self.build_texture_group()
        self.build_render_group()

        self.group.add(self.texture_group)
        self.group.add(self.render_group)

    def build_texture_group(
        self,
    ) -> None:
        if not self.stage.use_textures:
            return

        for binder in self.texture_binders.values():
            self.texture_group.add(binder)

    def build_render_group(
        self,
    ) -> None:
        self.render_group.add(
            self.transform_callback,
        )

        self.render_group.add(
            self.geometry_callback,
        )

        if self.stage.use_material:
            self.render_group.add(
                self.material_callback,
            )

        if self.object_id_callback is not None:
            self.render_group.add(
                self.object_id_callback,
            )

        self.render_group.add(
            self.mesh,
        )

    # =================================== #
    # Sync
    # =================================== #

    def sync_transform(
        self,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.transform_callback.sync(
            model_mat=model_mat,
            normal_mat=normal_mat,
        )

    def sync_uniforms(
        self,
        *_,
    ) -> None:
        if self.stage.use_material:
            self.material_callback.ask_update()

        if self.object_id_callback is not None:
            self.object_id_callback.ask_update()

    def sync_textures(
        self,
        *_,
    ) -> None:
        if not self.stage.use_textures:
            self.clear_texture_binders()
            return

        changed = False

        for name, slot in TEXTURE_SLOTS.items():
            texture = getattr(
                self.material,
                name,
                None,
            )

            binder = self.texture_binders.get(name)

            if texture is None:
                if binder is not None:
                    self.texture_binders.pop(name)
                    changed = True

                continue

            if binder is None:
                self.texture_binders[name] = BindTexture(
                    stage=self.stage,
                    uniform=name,
                    texture=texture,
                    slot=slot,
                )
                changed = True
                continue

            if binder.texture is not texture:
                binder.texture = texture
                binder.ask_update()

        if changed:
            self.rebuild()

        if self.stage.use_material:
            self.material_callback.ask_update()

    def clear_texture_binders(
        self,
    ) -> None:
        if not self.texture_binders:
            return

        self.texture_binders.clear()
        self.rebuild()

    def set_material(
        self,
        material: Material,
    ) -> None:
        self.material = material
        self.material_callback.material = material

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
        self.texture_binders.clear()
        self.texture_group.clear()
        self.render_group.clear()
        self.group.clear()



