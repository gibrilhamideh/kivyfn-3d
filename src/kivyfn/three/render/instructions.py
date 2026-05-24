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

        self.push = PushMatrix()
        self.matrix = MatrixInstruction()
        self.normal_matrix = UpdateNormalMatrix()

        material = object3d.material

        self.base_texture = BindTexture(
            texture=material.base_texture,
            index=1,
        )

        self.normal_texture = BindTexture(
            texture=material.normal_texture,
            index=2,
        )

        self.emissive_texture = BindTexture(
            texture=material.emissive_texture,
            index=3,
        )

        self.metallic_roughness_texture = BindTexture(
            texture=material.metallic_roughness_texture,
            index=4,
        )

        self.occlusion_texture = BindTexture(
            texture=material.occlusion_texture,
            index=5,
        )

        self.material_callback = Callback(
            partial(
                self.apply_material,
                material,
                ctx,
            )
        )

        geometry = object3d.geometry

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

        self.group.add(self.material_callback)
        self.group.add(self.mesh)
        self.group.add(self.pop)

        self.sync_transform()

        material.bind(
            uniforms=self.update_uniforms,
            base_texture=self.update_textures,
            normal_texture=self.update_textures,
            emissive_texture=self.update_textures,
            metallic_roughness_texture=self.update_textures,
            occlusion_texture=self.update_textures,
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
            if key == "base_texture":
                ctx[key] = 1

            elif key == "normal_texture":
                ctx[key] = 2

            elif key == "emissive_texture":
                ctx[key] = 3

            elif key == "metallic_roughness_texture":
                ctx[key] = 4

            elif key == "occlusion_texture":
                ctx[key] = 5

            else:
                ctx[key] = value

    def update_textures(self, *_):
        material = self.object3d.material

        self.base_texture.texture = material.base_texture
        self.normal_texture.texture = material.normal_texture
        self.emissive_texture.texture = material.emissive_texture
        self.metallic_roughness_texture.texture = (
            material.metallic_roughness_texture
        )
        self.occlusion_texture.texture = material.occlusion_texture

        self.material_callback.ask_update()

    def update_uniforms(self, *_):
        self.material_callback.ask_update()
