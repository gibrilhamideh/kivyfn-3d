from __future__ import annotations

from kivy.graphics import Mesh
from kivyfn.three.render.geometry import Geometry


class RenderMesh:
    def __init__(
        self,
        geometry: Geometry,
        mode: str = "triangles",
        texture=None,
    ):
        self.geometry = geometry
        self.mode = mode
        self.texture = texture

        self.instruction = Mesh(
            vertices=geometry.vertices,
            indices=geometry.indices,
            fmt=geometry.vertex_format,
            mode=mode,
            texture=texture,
        )

    def update_geometry(
        self,
        geometry: Geometry,
    ) -> None:
        self.geometry = geometry

        self.instruction.vertices = geometry.vertices
        self.instruction.indices = geometry.indices

    def update_texture(
        self,
        texture,
    ) -> None:
        self.texture = texture
        self.instruction.texture = texture

    def __repr__(self) -> str:
        return (
            f"RenderMesh("
            f"name={self.geometry.name!r}, "
            f"vertices={len(self.geometry.vertices)}, "
            f"indices={len(self.geometry.indices)})"
        )
