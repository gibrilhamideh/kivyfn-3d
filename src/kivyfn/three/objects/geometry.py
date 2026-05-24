# kiyvfn/three/render/geomerty.py
from __future__ import annotations
from typing import Literal
from dataclasses import dataclass, field
import numpy as np

from kivy.graphics.texture import Texture


RenderMode = Literal[
    "points",
    "line_strip",
    "line_loop",
    "lines",
    "triangles",
    "triangle_strip",
    "triangle_fan"
]

@dataclass(slots=True)
class GeometryStats:
    vertex_count: int
    index_count: int
    triangle_count: int

    is_watertight: bool
    is_volume: bool
    is_winding_consistent: bool
    euler_number: int

@dataclass(slots=True)
class Geometry:
    name: str | None = None

    fmt: list[tuple[bytes, int, str]] = field(default_factory=lambda: [
        (b"v_pos", 3, "float"),
        (b"v_normal", 3, "float"),
        (b"v_uv", 2, "float"),
        (b"v_tangent", 4, "float"),
    ])

    vertices: list[float] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)
    mode: RenderMode = "triangles"
    texture: Texture | None = None 
    has_source_tangents: bool = False

    @property
    def stride(self) -> int:
        return sum(
            size
            for _, size, _ in self.fmt
        )

    def get_stats(self, *, merge_vertices = False) -> GeometryStats:
        try:
            import trimesh
        except ImportError as error:
            raise ImportError(
                "Geometry.get_stats() requires trimesh. "
                "Install it with: pip install trimesh"
            ) from error

        stride = sum(
            size
            for _, size, _ in self.fmt
        )

        vertices = np.array(
            self.vertices,
            dtype=np.float32,
        ).reshape(-1, stride)

        positions = vertices[:, :3]

        indices = np.array(
            self.indices,
            dtype=np.int64,
        )

        triangle_count = len(indices) // 3

        faces = indices.reshape(-1, 3)

        mesh = trimesh.Trimesh(
            vertices=positions,
            faces=faces,
            process=False,
        )

        if merge_vertices:
            mesh.merge_vertices()
            mesh.remove_unreferenced_vertices()
            mesh.fix_normals()

        return GeometryStats(
            vertex_count=len(positions),
            index_count=len(indices),
            triangle_count=triangle_count,
            is_watertight=bool(mesh.is_watertight),
            is_volume=bool(mesh.is_volume),
            is_winding_consistent=bool(mesh.is_winding_consistent),
            euler_number=int(mesh.euler_number),
        )

