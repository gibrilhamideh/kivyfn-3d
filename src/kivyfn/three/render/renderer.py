# kivyfn/three/render/renderer.py

from __future__ import annotations

from functools import partial

from kivy.graphics import (
    Callback,
    PopMatrix,
    PushMatrix,
    Rotate,
    Scale,
    Translate,
    UpdateNormalMatrix,
    RenderContext
)

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.render.material import Material
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.object3d import Object3D
from kivyfn.three.scene.node import Node3D


class Renderer:
    def __init__(
        self,
        render_ctx: RenderContext,
        shader: Shader,
    ):
        self.render_ctx = render_ctx
        self.shader = shader
        self._active_shader: Shader | None = None

    def __repr__(self) -> str:
        return f"Renderer(shader={self.shader!r})"

    def render(self, root: Node3D) -> None:
        self._active_shader = None
        self._render(root)

    def _render(self, node: Node3D) -> None:
        if not node.visible:
            return

        PushMatrix()
        self._apply_transform(node)

        node.render(self)

        for child in node.children:
            self._render(child)

        PopMatrix()

    def render_object(self, object3d: Object3D) -> None:
        if object3d.mesh_data is None:
            return

        material = object3d.material
        shader = material.shader or self.shader

        self._use_shader(shader)

        Callback(partial(self._apply_material, material))

        if object3d.render_mesh is None:
            object3d.render_mesh = RenderMesh(mesh_data=object3d.mesh_data, mode=object3d.render_mode)
        else:
            object3d.render_mesh.update_mesh_data(object3d.mesh_data)

        self.render_ctx.add(object3d.render_mesh.instruction)

    def _apply_material(self, material: Material, *args) -> None:
        material.apply_to(self.render_ctx)

    def _apply_transform(self, node: Node3D) -> None:
        transform = node.transform

        tx, ty, tz = transform.translation
        sx, sy, sz = transform.scale

        rotation = transform.rotation
        if not isinstance(rotation, Quaternion):
            rotation = Quaternion(*rotation)

        axis_x, axis_y, axis_z, angle = rotation.to_axis_angle()

        Translate(tx, ty, tz)
        Rotate(angle=angle, axis=(axis_x, axis_y, axis_z))
        Scale(sx, sy, sz)

        UpdateNormalMatrix()

    def _use_shader(self, shader: Shader) -> None:
        if shader is self._active_shader:
            return

        shader.apply_to(self.render_ctx)
        self._active_shader = shader

    # =================================== #
    # View
    # =================================== #
    def update_view(self, camera, aspect) -> None:
        self.render_ctx["projection_mat"] = camera.get_projection_matrix(aspect)
        self.render_ctx["modelview_mat"] = camera.get_view_matrix()

    @property
    def projection_mat(self):
        return self.render_ctx["projection_mat"]

    @property
    def modelview_mat(self):
        return self.render_ctx["modelview_mat"]



    
