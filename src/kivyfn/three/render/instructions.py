# kivyfn/three/render/object.py

from __future__ import annotations

from functools import partial

from kivy.graphics import (
    Callback,
    InstructionGroup,
    PopMatrix,
    PushMatrix,
    Rotate,
    Scale,
    Translate,
    UpdateNormalMatrix,
)

from kivyfn.three.render.material import Material
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.render.context import RenderContext
from kivyfn.three.scene.object3d import Object3D


class Instructions:
    def __init__(
        self,
        object3d: Object3D,
        ctx: RenderContext,
    ):
        self.object3d = object3d
        self.ctx = ctx
        self.group = InstructionGroup()

        self.push = PushMatrix()
        self.translate = Translate(0.0, 0.0, 0.0)
        self.rotate = Rotate(angle=0.0, axis=(0.0, 0.0, 1.0))
        self.scale = Scale(1.0, 1.0, 1.0)
        self.normal_matrix = UpdateNormalMatrix()
        self.material_callback = Callback(
            partial(
                self._apply_material,
                object3d.material,
                ctx,
            )
        )
        self.mesh = RenderMesh(
            mesh_data=object3d.mesh_data,
            mode=object3d.render_mode,
        )
        self.pop = PopMatrix()

        self.group.add(self.push)
        self.group.add(self.translate)
        self.group.add(self.rotate)
        self.group.add(self.scale)
        self.group.add(self.normal_matrix)
        self.group.add(self.material_callback)
        self.group.add(self.mesh.instruction)
        self.group.add(self.pop)

    def update_material(self) -> None:
        self.material_callback = Callback(
            partial(
                self._apply_material,
                self.object3d.material,
                self.ctx,
            )
        )

    def _apply_material(
        self,
        material: Material,
        ctx: RenderContext,
        *args,
    ) -> None:
        material.apply_to(ctx=ctx)
