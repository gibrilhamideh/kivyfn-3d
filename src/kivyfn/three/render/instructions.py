# kivyfn/three/render/instructions.py

from __future__ import annotations

from functools import partial
from typing import Any, Callable, TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics import (
    BindTexture,
    Callback,
    InstructionGroup,
    MatrixInstruction,
    Mesh,
    PopMatrix,
    PushMatrix,
    UpdateNormalMatrix,
)

if TYPE_CHECKING:
    from kivy.graphics.transformation import Matrix

    from kivyfn.three.objects.geometry import Geometry
    from kivyfn.three.objects.material import Material


ApplyUniform = Callable[[str, Any], None]


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
        compute_normal_matrix: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.geometry = geometry
        self.visible = True

        self.group = InstructionGroup()

        self.push = PushMatrix()
        self.matrix = MatrixInstruction()

        self.normal_matrix = None
        if compute_normal_matrix:
            self.normal_matrix = UpdateNormalMatrix()

        self.mesh = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.fmt,
            mode=geometry.mode,
            texture=geometry.texture,
        )

        self.pop = PopMatrix()

        self.instructions = [
            self.push,
            self.matrix,
            self.normal_matrix,
            self.mesh,
            self.pop,
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
        matrix: Matrix,
    ) -> None:
        self.matrix.matrix = matrix

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
        apply_uniform: ApplyUniform,
    ):
        super().__init__(
            geometry=geometry,
            compute_normal_matrix=True,
        )

        self.material = material
        self.apply_uniform = apply_uniform

        self.texture_binders = {
            name: BindTexture(index=slot)
            for name, slot in TEXTURE_SLOTS.items()
        }

        self.material_callback = Callback(
            partial(
                self.apply_material,
                material,
            )
        )

        self.instructions = [
            self.push,
            self.matrix,
            self.normal_matrix,
            *self.texture_binders.values(),
            self.material_callback,
            self.mesh,
            self.pop,
        ]

        self.rebuild()
        self.sync_uniforms()
        self.sync_textures()

    def copy(self) -> MaterialInstructions:
        return self.__class__(
            geometry=self.geometry,
            material=self.material,
            apply_uniform=self.apply_uniform,
        )

    def apply_material(
        self,
        material: Material,
        callback: Callback,
    ) -> None:
        for key, value in material.uniforms.items():
            if value is None:
                continue

            if key in TEXTURE_SLOTS:
                self.apply_uniform(key, TEXTURE_SLOTS[key])
                continue

            self.apply_uniform(key, value)

    def sync_textures(self, *_):
        for name, binder in self.texture_binders.items():
            texture = getattr(self.material, name, None)

            if texture is not None:
                binder.texture = texture

        self.material_callback.ask_update()

    def sync_uniforms(self, *_):
        self.material_callback.ask_update()

    def destroy(self) -> None:
        super().destroy()


class ColorInstructions(MaterialInstructions):
    pass


class ObjectIdInstructions(BaseInstructions):
    def __init__(
        self,
        *,
        geometry: Geometry,
        object_id: int,
        apply_uniform: ApplyUniform,
    ):
        super().__init__(geometry=geometry)

        self.object_id = object_id
        self.apply_uniform = apply_uniform
        self.object_id_callback = Callback(self.apply_object_id)

        self.instructions = [
            self.push,
            self.matrix,
            self.object_id_callback,
            self.mesh,
            self.pop,
        ]

        self.rebuild()



    def apply_object_id(
        self,
        callback: Callback,
    ) -> None:
        object_id = self.object_id

        r = (object_id >> 16) & 0xFF
        g = (object_id >> 8) & 0xFF
        b = object_id & 0xFF

        self.apply_uniform(
            "object_id_color",
            [
                r / 255.0,
                g / 255.0,
                b / 255.0,
                1.0,
            ],
        )


class NormalInstructions(BaseInstructions):
    def __init__(
        self,
        *,
        geometry: Geometry,
    ):
        super().__init__(
            geometry=geometry,
            compute_normal_matrix=True,
        )


class DepthInstructions(BaseInstructions):
    pass


class PositionInstructions(BaseInstructions):
    pass
