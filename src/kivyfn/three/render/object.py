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

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.render.material import Material
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.render.render_pass import RenderPass
from kivyfn.three.scene.object3d import Object3D


class RenderObject:
    def __init__(
        self,
        object3d: Object3D,
        render_pass: RenderPass,
    ):
        self.object3d = object3d
        self.render_pass = render_pass

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
                render_pass,
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

        self.update_transform()

    def add_to_pass(self) -> None:
        self.render_pass.context.add(self.group)

    def remove_from_pass(self) -> None:
        self.render_pass.context.remove(self.group)

    def update_transform(self) -> None:
        transform = self.object3d.transform

        tx, ty, tz = transform.translation
        sx, sy, sz = transform.scale

        rotation: Quaternion = transform.rotation
        axis_x, axis_y, axis_z, angle = rotation.to_axis_angle()

        self.translate.x = tx
        self.translate.y = ty
        self.translate.z = tz

        self.rotate.angle = angle
        self.rotate.axis = (axis_x, axis_y, axis_z)

        self.scale.x = sx
        self.scale.y = sy
        self.scale.z = sz

    def update_mesh(self) -> None:
        if self.object3d.mesh_data is None:
            return

        self.mesh.update_mesh_data(self.object3d.mesh_data)

    def update_material(self) -> None:
        self.material_callback = Callback(
            partial(
                self._apply_material,
                self.object3d.material,
                self.render_pass,
            )
        )

    def _apply_material(
        self,
        material: Material,
        render_pass: RenderPass,
        *args,
    ) -> None:
        material.apply_to(render_pass.context)
