# kivyfn/three/render/instances.py

from __future__ import annotations

from typing import TYPE_CHECKING, overload
from collections import defaultdict

from kivy.event import EventDispatcher

from kivy.event import EventDispatcher
from kivy.graphics import (
    BindTexture,
    InstructionGroup,
    Mesh,
)

from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.render.callbacks import (
    MaterialCallback,
    ObjectIdCallback,
    TransformCallback,
)

if TYPE_CHECKING:
    from kivyfn.three.types import RenderStage
    from kivyfn.three.assets.geometry import Geometry
    from kivyfn.three.assets.material import Material
    from kivyfn.three.render.context import RenderContext


TEXTURE_SLOTS = {
    "base_texture": 1,
    "normal_texture": 2,
    "emissive_texture": 3,
    "metallic_roughness_texture": 4,
    "occlusion_texture": 5,
    "roughness_texture": 6,
    "metallic_texture": 7,
    "specular_texture": 8,
    "displacement_texture": 9,
}


from kivyfn.three.render.context import RenderContext, RenderPass2D, RenderPassCube

if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.types import RenderPassOutput, RenderStage


class RenderInstanceManager(EventDispatcher):
    """
    Owns render instances for object/stage pairs.

    A render instance is:

        Object3D + RenderStage -> BaseInstance

    Each instance owns the concrete Kivy graphics instruction group needed
    to render one object in one stage.

    This manager does NOT decide which objects belong to which stages.
    That belongs to Renderer and the render registries.

    Internal indexes:
    - object_id -> stage_name -> instance
    - stage_name -> object_id -> instance
    """

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
        "on_visibility_dirty",
    )

    def __init__(self) -> None:
        super().__init__()

        self._instances_by_object: defaultdict[int, dict[str, BaseInstance]] = defaultdict(dict)
        self._instances_by_stage: defaultdict[str, dict[int, BaseInstance]] = defaultdict(dict)

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
    ) -> dict[str, BaseInstance]:
        ...

    @overload
    def instances_of(
        self,
        *,
        object3d: None = None,
        stage_name: str,
    ) -> dict[int, BaseInstance]:
        ...

    def instances_of(
        self,
        *,
        object3d: Object3D | None = None,
        stage_name: str | None = None,
    ) -> dict[str, BaseInstance] | dict[int, BaseInstance]:
        if object3d is None and stage_name is None:
            raise ValueError(
                "instances_of() requires either 'object3d' or 'stage_name'."
            )

        if object3d is not None and stage_name is not None:
            raise ValueError(
                "instances_of() accepts either 'object3d' or 'stage_name', not both."
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
    ) -> BaseInstance:
        object_id = id(object3d)
        stage_name = stage.name

        existing = self._instances_by_object[object_id].get(stage_name)
        if existing is not None:
            return existing

        instance = self._create_instance(
            object3d=object3d,
            stage=stage,
        )

        stage.add(instance.group)

        self._objects[object_id] = object3d
        self._instances_by_object[object_id][stage_name] = instance
        self._instances_by_stage[stage_name][object_id] = instance

        self.bind_object(object3d)

        return instance

    def _create_instance(
        self,
        object3d: Object3D,
        stage: RenderStage,
    ) -> BaseInstance:
        if isinstance(stage, RenderContext):
            return MaterialInstance(
                geometry=object3d.geometry,
                material=object3d.material,
                stage=stage,
            )

        return self._create_pass_instance(
            object3d=object3d,
            stage=stage,
            output=stage.output,
            output_uniform=stage.output_uniform,
        )

    def _create_pass_instance(
        self,
        object3d: Object3D,
        stage: RenderPass2D | RenderPassCube,
        output: RenderPassOutput,
        output_uniform: str,
    ) -> BaseInstance:
        if output == "depth":
            return DepthInstance(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "position":
            return PositionInstance(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "normal":
            return NormalInstance(
                geometry=object3d.geometry,
                stage=stage,
                output_uniform=output_uniform,
            )

        if output == "id":
            return ObjectIdInstance(
                geometry=object3d.geometry,
                render_id=object3d.require_render_id(),
                stage=stage,
                output_uniform=output_uniform,
            )

        return ColorInstance(
            geometry=object3d.geometry,
            stage=stage,
            output_uniform=output_uniform,
        )

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
            if isinstance(instance, MaterialInstance):
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





class BaseInstance(EventDispatcher):
    def __init__(
        self,
        *,
        geometry: Geometry,
        stage: RenderStage,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.stage = stage
        self.geometry = geometry
        self.visible = True

        self.group = InstructionGroup()

        self.transform_callback = TransformCallback(
            stage=stage,
        )

        self.mesh = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.fmt,
            mode=geometry.mode,
            texture=geometry.texture,
        )

        self.instructions = [
            self.transform_callback,
            self.mesh,
        ]

        self.rebuild()

    def rebuild(self) -> None:
        self.group.clear()

        if not self.visible:
            return

        for instruction in self.instructions:
            if instruction is not None:
                self.group.add(instruction)

    def sync_transform(
        self,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.transform_callback.sync(
            model_mat=model_mat,
            normal_mat=normal_mat,
        )

    def sync_uniforms(self, *_):
        pass

    def sync_textures(self, *_):
        pass

    def show(self) -> None:
        if self.visible:
            return

        self.visible = True
        self.rebuild()

    def hide(self) -> None:
        if not self.visible:
            return

        self.visible = False
        self.rebuild()

    def destroy(self) -> None:
        self.group.clear()
        self.instructions.clear()


class MaterialInstance(BaseInstance):
    def __init__(
        self,
        *,
        geometry: Geometry,
        material: Material,
        stage: RenderContext,
    ):
        super().__init__(
            geometry=geometry,
            stage=stage,
        )

        self.material = material

        self.texture_binders = {
            name: BindTexture(index=slot)
            for name, slot in TEXTURE_SLOTS.items()
        }

        self.material_callback = MaterialCallback(
            stage=stage,
            material=material,
            texture_slots=TEXTURE_SLOTS,
        )

        self.instructions = [
            self.transform_callback,
            *self.texture_binders.values(),
            self.material_callback,
            self.mesh,
        ]

        self.rebuild()
        self.sync_uniforms()
        self.sync_textures()

    def sync_textures(self, *_):
        # BUG:
        # Texture binders are never cleared when a material texture
        # becomes None. This may leave a previously bound texture
        # active in OpenGL state. Need a strategy for handling
        # missing textures (default textures vs use_* uniforms flags).
        for name, binder in self.texture_binders.items():
            texture = getattr(self.material, name, None)

            if texture is not None:
                binder.texture = texture

        self.material_callback.ask_update()

    def sync_uniforms(self, *_):
        self.material_callback.ask_update()

    def set_material(
        self,
        material: Material,
    ) -> None:
        self.material = material
        self.material_callback.material = material

        self.sync_uniforms()
        self.sync_textures()

class BasePassInstance(BaseInstance):
    def __init__(
        self,
        *,
        output_uniform: str,
        **kwargs
    ):

        self.output_uniform = output_uniform
        super().__init__(**kwargs)


class ObjectIdInstance(BasePassInstance):
    def __init__(
        self,
        *,
        render_id: int,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.render_id = render_id
        self.object_id_callback = ObjectIdCallback(
            stage=self.stage,
            render_id=self.render_id,
            output_uniform=self.output_uniform
        )

        self.instructions = [
            self.transform_callback,
            self.object_id_callback,
            self.mesh,
        ]

        self.rebuild()

    def sync_uniforms(self, *_):
        self.object_id_callback.ask_update()

class ColorInstance(BasePassInstance):
    pass

class NormalInstance(BasePassInstance):
    pass

class DepthInstance(BasePassInstance):
    pass

class PositionInstance(BasePassInstance):
    pass



