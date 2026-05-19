# kivyfn/three/render/renderer.py

from __future__ import annotations

from kivy.graphics import (
    PopMatrix,
    PushMatrix,
    Rotate,
    Scale,
    Translate,
    UpdateNormalMatrix,
)

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.render.mesh import RenderMesh
from kivyfn.three.scene.meshnode import MeshNode
from kivyfn.three.scene.node import Node3D


class Renderer:
    def __init__(self):
        self.render_meshes: dict[MeshNode, RenderMesh] = {}

    def render(self, root: Node3D) -> None:
        self.render_meshes.clear()
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

        render_mesh = RenderMesh(mesh_data=node.mesh_data)
        self.render_meshes[node] = render_mesh

    def __repr__(self) -> str:
        return f"Renderer(render_meshes={len(self.render_meshes)})"
