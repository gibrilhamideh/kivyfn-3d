# kivyfn/three/render/geometry.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from kivy.graphics.texture import Texture


RenderMode = Literal[
    "points",
    "line_strip",
    "line_loop",
    "lines",
    "triangles",
    "triangle_strip",
    "triangle_fan",
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

    fmt: list[tuple[bytes, int, str]] = field(
        default_factory=lambda: [
            (b"v_pos", 3, "float"),
            (b"v_normal", 3, "float"),
            (b"v_uv", 2, "float"),
            (b"v_tangent", 4, "float"),
        ]
    )

    vertices: NDArray[np.float32] = field(
        default_factory=lambda: np.array(
            [],
            dtype=np.float32,
        )
    )

    indices: NDArray[np.uint16] = field(
        default_factory=lambda: np.array(
            [],
            dtype=np.uint16,
        )
    )

    mode: RenderMode = "triangles"

    texture: Texture | None = None

    has_source_tangents: bool = False

    def __repr__(self) -> str:
        return (
            "Geometry(\n"
            f"  name={self.name!r},\n"
            f"  vertex_count={self.vertex_count},\n"
            f"  float_count={len(self.vertices)},\n"
            f"  index_count={self.index_count},\n"
            f"  triangle_count={self.triangle_count},\n"
            f"  stride={self.stride},\n"
            f"  mode={self.mode!r},\n"
            f"  has_texture={self.texture is not None},\n"
            f"  has_source_tangents={self.has_source_tangents}\n"
            ")"
        )

    @property
    def stride(self) -> int:
        return sum(
            size
            for _, size, _ in self.fmt
        )

    @property
    def vertex_count(self) -> int:
        if self.stride <= 0:
            return 0

        return len(self.vertices) // self.stride

    @property
    def index_count(self) -> int:
        return len(self.indices)

    @property
    def triangle_count(self) -> int:
        if len(self.indices) > 0:
            return len(self.indices) // 3

        return self.vertex_count // 3

    def get_stats(
        self,
        *,
        merge_vertices: bool = False,
    ) -> GeometryStats:

        try:
            import trimesh

        except ImportError as error:
            raise ImportError(
                "Geometry.get_stats() requires trimesh. "
                "Install it with: pip install trimesh"
            ) from error

        vertices = self.vertices.reshape(
            -1,
            self.stride,
        )

        positions = vertices[:, :3]

        indices = self.indices.astype(
            np.int64,
            copy=False,
        )

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
            triangle_count=len(faces),
            is_watertight=bool(mesh.is_watertight),
            is_volume=bool(mesh.is_volume),
            is_winding_consistent=bool(mesh.is_winding_consistent),
            euler_number=int(mesh.euler_number),
        )
