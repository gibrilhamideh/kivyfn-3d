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
)

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.render.material import Material
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.meshnode import MeshNode
from kivyfn.three.scene.node import Node3D


class Renderer:
    def __init__(
        self,
        render_ctx,
        shader: Shader,
    ):
        self.render_ctx = render_ctx
        self.shader = shader
        self._active_shader: Shader | None = None

    def __repr__(self) -> str:
        return f"Renderer(shader={self.shader!r})"

    def render(self, root: Node3D) -> None:
        self._active_shader = None
        self._render_node(root)

    def _render_node(self, node: Node3D) -> None:
        if not node.visible:
            return

        PushMatrix()
        self._apply_transform(node)

        if isinstance(node, MeshNode):
            self._render_mesh_node(node)

        for child in node.children:
            self._render_node(child)

        PopMatrix()

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

    def _render_mesh_node(self, node: MeshNode) -> None:
        if node.mesh_data is None:
            return

        material = node.material
        shader = material.shader or self.shader

        self._use_shader(shader)

        Callback(partial(self._apply_material, material))
        RenderMesh(mesh_data=node.mesh_data)

    def _use_shader(self, shader: Shader) -> None:
        if shader is self._active_shader:
            return

        shader.apply_to(self.render_ctx)
        self._active_shader = shader

    def _apply_material(self, material: Material, *args) -> None:
        material.apply_to(self.render_ctx)
