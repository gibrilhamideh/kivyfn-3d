# kivyfn/three/render/instructions.py

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

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
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.objects.material import Material
    from kivyfn.three.objects.object3d import Object3D


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


class Instructions(EventDispatcher):
    def __init__(
        self,
        object3d: Object3D,
        ctx: RenderContext,
    ):
        super().__init__()

        self.ctx = ctx
        self.group = InstructionGroup()
        self.object3d = object3d

        material = object3d.material
        geometry = object3d.geometry

        self.push = PushMatrix()
        self.matrix = MatrixInstruction()
        self.normal_matrix = UpdateNormalMatrix()

        self.base_texture = BindTexture(index=1)
        self.normal_texture = BindTexture(index=2)
        self.emissive_texture = BindTexture(index=3)
        self.metallic_roughness_texture = BindTexture(index=4)
        self.occlusion_texture = BindTexture(index=5)
        self.roughness_texture = BindTexture(index=6)
        self.metallic_texture = BindTexture(index=7)
        self.specular_texture = BindTexture(index=8)
        self.displacement_texture = BindTexture(index=9)

        self.material_callback = Callback(
            partial(
                self.apply_material,
                material,
                ctx,
            )
        )

        self.mesh = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.fmt,
            mode=geometry.mode,
            texture=geometry.texture,
        )

        self.pop = PopMatrix()

        self.group.add(self.push)
        self.group.add(self.matrix)
        self.group.add(self.normal_matrix)

        self.group.add(self.base_texture)
        self.group.add(self.normal_texture)
        self.group.add(self.emissive_texture)
        self.group.add(self.metallic_roughness_texture)
        self.group.add(self.occlusion_texture)
        self.group.add(self.roughness_texture)
        self.group.add(self.metallic_texture)
        self.group.add(self.specular_texture)
        self.group.add(self.displacement_texture)

        self.group.add(self.material_callback)
        self.group.add(self.mesh)
        self.group.add(self.pop)

        self.sync_transform()
        self.update_textures()

        material.bind(
            uniforms=self.update_uniforms,
            base_texture=self.update_textures,
            normal_texture=self.update_textures,
            emissive_texture=self.update_textures,
            metallic_roughness_texture=self.update_textures,
            occlusion_texture=self.update_textures,
            roughness_texture=self.update_textures,
            metallic_texture=self.update_textures,
            specular_texture=self.update_textures,
            displacement_texture=self.update_textures,
        )

    def sync_transform(self) -> None:
        self.matrix.matrix = self.object3d.world_matrix.to_kivy_matrix()

    def apply_material(
        self,
        material: Material,
        ctx: RenderContext,
        callback: Callback,
    ) -> None:
        for key, value in material.uniforms.items():
            if value is None:
                continue

            if key in TEXTURE_SLOTS:
                ctx[key] = TEXTURE_SLOTS[key]
                continue

            ctx[key] = value

    def update_textures(self, *_):
        material = self.object3d.material

        if material.base_texture is not None:
            self.base_texture.texture = material.base_texture

        if material.normal_texture is not None:
            self.normal_texture.texture = material.normal_texture

        if material.emissive_texture is not None:
            self.emissive_texture.texture = material.emissive_texture

        if material.metallic_roughness_texture is not None:
            self.metallic_roughness_texture.texture = (
                material.metallic_roughness_texture
            )

        if material.occlusion_texture is not None:
            self.occlusion_texture.texture = material.occlusion_texture

        if material.roughness_texture is not None:
            self.roughness_texture.texture = material.roughness_texture

        if material.metallic_texture is not None:
            self.metallic_texture.texture = material.metallic_texture

        if material.specular_texture is not None:
            self.specular_texture.texture = material.specular_texture

        if material.displacement_texture is not None:
            self.displacement_texture.texture = material.displacement_texture

        self.material_callback.ask_update()

    def update_uniforms(self, *_):
        self.material_callback.ask_update()
