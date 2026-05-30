# kivyfn/three/render/instructions.py

from __future__ import annotations

from typing import TYPE_CHECKING

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
    from kivyfn.three.objects.geometry import Geometry
    from kivyfn.three.objects.material import Material
    from kivyfn.three.render.context import RenderContext, RenderPass


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


class BaseInstructions(EventDispatcher):
    def __init__(
        self,
        *,
        geometry: Geometry,
        ctx: RenderContext | RenderPass,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.ctx = ctx
        self.geometry = geometry
        self.visible = True

        self.group = InstructionGroup()

        self.transform_callback = TransformCallback(
            ctx=ctx,
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


class MaterialInstructions(BaseInstructions):
    def __init__(
        self,
        *,
        geometry: Geometry,
        material: Material,
        ctx: RenderContext,
    ):
        super().__init__(
            geometry=geometry,
            ctx=ctx,
        )

        ctx["shadow_texture"] = 10

        self.material = material

        self.texture_binders = {
            name: BindTexture(index=slot)
            for name, slot in TEXTURE_SLOTS.items()
        }

        self.material_callback = MaterialCallback(
            ctx=ctx,
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
        for name, binder in self.texture_binders.items():
            texture = getattr(self.material, name, None)

            if texture is not None:
                binder.texture = texture

        self.material_callback.ask_update()

    def sync_uniforms(self, *_):
        self.material_callback.ask_update()


class ColorInstructions(BaseInstructions):
    def __init__(
        self,
        *,
        geometry: Geometry,
        ctx: RenderPass,
    ):
        super().__init__(
            geometry=geometry,
            ctx=ctx,
        )


class ObjectIdInstructions(BaseInstructions):
    def __init__(
        self,
        *,
        geometry: Geometry,
        object_id: int,
        ctx: RenderPass,
    ):
        super().__init__(
            geometry=geometry,
            ctx=ctx,
        )

        self.object_id = object_id

        self.object_id_callback = ObjectIdCallback(
            ctx=ctx,
            object_id=object_id,
        )

        self.instructions = [
            self.transform_callback,
            self.object_id_callback,
            self.mesh,
        ]

        self.rebuild()

    def sync_uniforms(self, *_):
        self.object_id_callback.ask_update()


class NormalInstructions(BaseInstructions):
    pass


class DepthInstructions(BaseInstructions):
    pass


class PositionInstructions(BaseInstructions):
    pass
