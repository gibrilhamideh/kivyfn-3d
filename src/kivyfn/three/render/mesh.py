from __future__ import annotations

from kivy.graphics import Mesh
from kivyfn.three.render.meshdata import MeshData


class RenderMesh:
    def __init__(
        self,
        mesh_data: MeshData,
        mode: str = "triangles",
        texture=None,
    ):
        self.mesh_data = mesh_data
        self.mode = mode
        self.texture = texture

        self.instruction = Mesh(
            vertices=mesh_data.vertices,
            indices=mesh_data.indices,
            fmt=mesh_data.vertex_format,
            mode=mode,
            texture=texture,
        )

    def update_mesh_data(
        self,
        mesh_data: MeshData,
    ) -> None:
        self.mesh_data = mesh_data

        self.instruction.vertices = mesh_data.vertices
        self.instruction.indices = mesh_data.indices

    def update_texture(
        self,
        texture,
    ) -> None:
        self.texture = texture
        self.instruction.texture = texture

    def __repr__(self) -> str:
        return (
            f"RenderMesh("
            f"name={self.mesh_data.name!r}, "
            f"vertices={len(self.mesh_data.vertices)}, "
            f"indices={len(self.mesh_data.indices)})"
        )
