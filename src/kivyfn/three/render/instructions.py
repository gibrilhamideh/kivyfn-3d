# kivyfn/three/render/instructions.py

from __future__ import annotations

from typing import TYPE_CHECKING
from functools import partial

from kivy.event import EventDispatcher
from kivy.graphics import (
    Callback,
    InstructionGroup,
    MatrixInstruction,
    Mesh,
    PopMatrix,
    PushMatrix,
    UpdateNormalMatrix,
)

if TYPE_CHECKING:
    from kivyfn.three.objects import Object3D, Material
    from kivyfn.three.render.context import RenderContext


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

        self.material_callback = Callback(
            partial(
                self.apply_material,
                object3d.material,
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
        self.group.add(self.material_callback)
        self.group.add(self.mesh)
        self.group.add(self.pop)

        self.sync_transform()

        self.object3d.material.bind(
            uniforms=self.update_uniforms,
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
            ctx[key] = value

    def update_uniforms(self, *_):
        self.material_callback.ask_update()
