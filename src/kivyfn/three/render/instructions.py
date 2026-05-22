# kivyfn/three/render/instructions.py

from __future__ import annotations
from typing import TYPE_CHECKING
from functools import partial

from kivy.event import EventDispatcher
from kivy.graphics import (
    Callback,
    InstructionGroup,
    PopMatrix,
    PushMatrix,
    Rotate,
    Scale,
    Translate,
    Mesh,
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
        self.ctx = ctx
        self.group = InstructionGroup()
        self.object3d = object3d

        self.push = PushMatrix()
        self.translate = Translate(0.0, 0.0, 0.0)
        self.rotate = Rotate(angle=0.0, axis=(0.0, 0.0, 1.0))
        self.scale = Scale(1.0, 1.0, 1.0)
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
        self.group.add(self.translate)
        self.group.add(self.rotate)
        self.group.add(self.scale)
        self.group.add(self.normal_matrix)
        self.group.add(self.material_callback)
        self.group.add(self.mesh)
        self.group.add(self.pop)


        self.object3d.material.bind(uniforms=self.update_uniforms)


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
