# kivyfn/three/assets/geometry.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from kivy.graphics.texture import Texture

from kivyfn.three.math.vector import Vector3


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
class GeometryBounds:
    min: Vector3 = field(default_factory=Vector3.zero)
    max: Vector3 = field(default_factory=Vector3.zero)

    center: Vector3 = field(default_factory=Vector3.zero)
    size: Vector3 = field(default_factory=Vector3.zero)

    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0

    radius: float = 0.0

    top: Vector3 = field(default_factory=Vector3.zero)
    bottom: Vector3 = field(default_factory=Vector3.zero)

    left: Vector3 = field(default_factory=Vector3.zero)
    right: Vector3 = field(default_factory=Vector3.zero)

    front: Vector3 = field(default_factory=Vector3.zero)
    back: Vector3 = field(default_factory=Vector3.zero)

    @classmethod
    def from_positions(
        cls,
        positions: NDArray[np.float32],
    ) -> GeometryBounds:
        if positions.size == 0:
            return cls()

        mins = positions.min(axis=0)
        maxs = positions.max(axis=0)

        center = (mins + maxs) * 0.5
        size = maxs - mins

        x_min, y_min, z_min = mins
        x_max, y_max, z_max = maxs
        center_x, center_y, center_z = center

        radius = float(
            np.linalg.norm(
                positions - center,
                axis=1,
            ).max()
        )

        return cls(
            min=Vector3(float(x_min), float(y_min), float(z_min)),
            max=Vector3(float(x_max), float(y_max), float(z_max)),

            center=Vector3(float(center_x), float(center_y), float(center_z)),
            size=Vector3(float(size[0]), float(size[1]), float(size[2])),

            width=float(size[0]),
            height=float(size[1]),
            depth=float(size[2]),

            radius=radius,

            top=Vector3(float(center_x), float(y_max), float(center_z)),
            bottom=Vector3(float(center_x), float(y_min), float(center_z)),

            left=Vector3(float(x_min), float(center_y), float(center_z)),
            right=Vector3(float(x_max), float(center_y), float(center_z)),

            front=Vector3(float(center_x), float(center_y), float(z_max)),
            back=Vector3(float(center_x), float(center_y), float(z_min)),
        )


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

    bounds: GeometryBounds = field(
        default_factory=GeometryBounds,
    )

    def __post_init__(self) -> None:
        if self.vertices.size > 0:
            self.compute_bounds()

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
            f"  has_source_tangents={self.has_source_tangents},\n"
            f"  bounds={self.bounds}\n"
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

    def get_positions(self) -> NDArray[np.float32]:
        if self.vertices.size == 0 or self.stride <= 0:
            return np.empty(
                (0, 3),
                dtype=np.float32,
            )

        vertex_data = self.vertices.reshape(
            -1,
            self.stride,
        )

        return vertex_data[:, :3]

    def compute_bounds(self) -> GeometryBounds:
        self.bounds = GeometryBounds.from_positions(
            self.get_positions()
        )

        return self.bounds

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

        positions = self.get_positions()

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
