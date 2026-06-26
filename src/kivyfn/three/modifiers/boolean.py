from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import numpy as np

from kivyfn.three.backends.trimesh import require_boolean_backend
from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.assets.geometry import Geometry


BooleanOperation = Literal[
    "difference",
    "union",
    "intersection",
]

BooleanEngine = Literal[
    "manifold",
    "blender",
]

GeometryLike = Geometry | Object3D

MAX_MESH_INDEX = 65_535


class BooleanModifierError(RuntimeError):
    pass


class BooleanModifier:
    def __init__(
        self,
        cutter: GeometryLike | None = None,
        *,
        cutters: Iterable[GeometryLike] | None = None,
        operation: BooleanOperation = "difference",
        engine: BooleanEngine = "manifold",
        check_volume: bool = True,
        process: bool = True,
        flat_shading: bool = True,
        keep_texture: bool = False,
        name: str | None = None,
    ) -> None:
        self.engine: BooleanEngine = engine
        self.operation = operation
        self.check_volume = check_volume
        self.process = process
        self.flat_shading = flat_shading
        self.keep_texture = keep_texture
        self.name = name

        self.cutters: list[GeometryLike] = []

        if cutter is not None:
            self.cutters.append(cutter)

        if cutters is not None:
            self.cutters.extend(cutters)

        self._validate_operation()
        self._validate_engine()

    def add_cutter(self, cutter: GeometryLike) -> None:
        self.cutters.append(cutter)

    def remove_cutter(self, cutter: GeometryLike) -> None:
        self.cutters.remove(cutter)

    def clear_cutters(self) -> None:
        self.cutters.clear()

    def apply(
        self,
        geometry: Geometry,
        *,
        cutters: Iterable[GeometryLike] | None = None,
    ) -> Geometry:
        active_cutters = list(cutters) if cutters is not None else self.cutters

        if not active_cutters:
            return _copy_geometry(geometry)

        cutter_geometries = [
            _extract_geometry(cutter)
            for cutter in active_cutters
        ]

        return self._apply_geometries(
            base_geometry=geometry,
            cutter_geometries=cutter_geometries,
        )

    def apply_to_object(
        self,
        base: Object3D,
        *,
        cutters: Iterable[GeometryLike] | None = None,
        material: Material | None = None,
        name: str | None = None,
    ) -> Object3D:
        active_cutters = list(cutters) if cutters is not None else self.cutters

        if not active_cutters:
            result_geometry = _copy_geometry(base.geometry)
        else:
            cutter_geometries = [
                self._cutter_to_base_local_geometry(
                    base=base,
                    cutter=cutter,
                )
                for cutter in active_cutters
            ]

            result_geometry = self._apply_geometries(
                base_geometry=base.geometry,
                cutter_geometries=cutter_geometries,
            )

        result_name = (
            name
            if name is not None
            else self.name
            if self.name is not None
            else f"{base.name}_boolean"
        )

        return Object3D(
            name=result_name,
            geometry=result_geometry,
            material=material or base.material,
            transform=base.transform.copy(),
            pivot=base.pivot,
        )

    def _apply_geometries(
        self,
        *,
        base_geometry: Geometry,
        cutter_geometries: list[Geometry],
    ) -> Geometry:
        trimesh = require_boolean_backend()

        base_mesh = _geometry_to_trimesh(
            base_geometry,
            process=self.process,
        )

        cutter_meshes = [
            _geometry_to_trimesh(
                geometry,
                process=self.process,
            )
            for geometry in cutter_geometries
        ]

        meshes = [
            base_mesh,
            *cutter_meshes,
        ]

        try:
            if self.operation == "difference":
                result_mesh = trimesh.boolean.difference(
                    meshes,
                    engine=self.engine,
                    check_volume=self.check_volume,
                )
            elif self.operation == "union":
                result_mesh = trimesh.boolean.union(
                    meshes,
                    engine=self.engine,
                    check_volume=self.check_volume,
                )
            elif self.operation == "intersection":
                result_mesh = trimesh.boolean.intersection(
                    meshes,
                    engine=self.engine,
                    check_volume=self.check_volume,
                )
            else:
                raise ValueError(
                    f"Unsupported boolean operation: {self.operation!r}"
                )
        except Exception as exc:
            raise BooleanModifierError(
                "Boolean operation failed. Make sure all meshes are "
                "watertight positive volumes. For walls, use a Box with "
                "thickness, not a flat Plane."
            ) from exc

        if result_mesh is None:
            raise BooleanModifierError(
                "Boolean operation returned no result."
            )

        return _trimesh_to_geometry(
            result_mesh,
            template=base_geometry,
            flat_shading=self.flat_shading,
            keep_texture=self.keep_texture,
            name=self.name or base_geometry.name,
        )

    def _cutter_to_base_local_geometry(
        self,
        *,
        base: Object3D,
        cutter: GeometryLike,
    ) -> Geometry:
        if isinstance(cutter, Geometry):
            return cutter

        if not isinstance(cutter, Object3D):
            raise TypeError(
                "Boolean cutters must be Geometry or Object3D instances."
            )

        base_inverse = base.world_matrix.inverse()
        matrix = base_inverse @ cutter.world_matrix

        return _transform_geometry(
            cutter.geometry,
            matrix,
        )

    def _validate_operation(self) -> None:
        if self.operation not in {
            "difference",
            "union",
            "intersection",
        }:
            raise ValueError(
                f"Invalid boolean operation: {self.operation!r}"
            )

    def _validate_engine(self) -> None:
        if self.engine != "manifold":
            raise ValueError(
                f"Invalid boolean engine: {self.engine!r}. "
                "Currently only 'manifold' is supported."
            )


def _geometry_to_trimesh(
    geometry: Geometry,
    *,
    process: bool,
):
    trimesh = require_boolean_backend()

    _validate_geometry(geometry)

    vertex_data = np.asarray(
        geometry.vertices,
        dtype=np.float64,
    ).reshape((-1, geometry.stride))

    vertices = vertex_data[:, 0:3].copy()

    faces = np.asarray(
        geometry.indices,
        dtype=np.int64,
    ).reshape((-1, 3))

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=False,
    )

    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()

    if process:
        mesh.process(validate=True)

    return mesh


def _trimesh_to_geometry(
    mesh,
    *,
    template: Geometry,
    flat_shading: bool,
    keep_texture: bool,
    name: str | None,
) -> Geometry:
    if getattr(mesh, "is_empty", False):
        raise BooleanModifierError(
            "Boolean operation produced empty geometry."
        )

    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()

    if flat_shading:
        vertices, indices = _build_flat_geometry_data(
            mesh,
            template=template,
        )
    else:
        vertices, indices = _build_smooth_geometry_data(
            mesh,
            template=template,
        )

    _validate_index_limit(indices)

    return Geometry(
        name=name,
        fmt=list(template.fmt),
        vertices=vertices,
        indices=indices,
        mode="triangles",
        texture=template.texture if keep_texture else None,
    )


def _build_flat_geometry_data(
    mesh,
    *,
    template: Geometry,
) -> tuple[np.ndarray, np.ndarray]:
    faces = np.asarray(
        mesh.faces,
        dtype=np.int64,
    )

    positions = np.asarray(
        mesh.vertices,
        dtype=np.float64,
    )

    face_normals = np.asarray(
        mesh.face_normals,
        dtype=np.float64,
    )

    vertices: list[float] = []
    indices: list[int] = []

    vertex_index = 0

    for face_index, face in enumerate(faces):
        normal = face_normals[face_index]
        tangent = _fallback_tangent(normal)

        for source_index in face:
            position = positions[source_index]

            vertices.extend(
                _pack_vertex(
                    template=template,
                    position=position,
                    normal=normal,
                    uv=(0.0, 0.0),
                    tangent=tangent,
                )
            )

            indices.append(vertex_index)
            vertex_index += 1

    return (
        np.asarray(
            vertices,
            dtype=np.float32,
        ),
        np.asarray(
            indices,
            dtype=np.uint16,
        ),
    )


def _build_smooth_geometry_data(
    mesh,
    *,
    template: Geometry,
) -> tuple[np.ndarray, np.ndarray]:
    positions = np.asarray(
        mesh.vertices,
        dtype=np.float64,
    )

    normals = np.asarray(
        mesh.vertex_normals,
        dtype=np.float64,
    )

    vertices: list[float] = []

    for position, normal in zip(positions, normals):
        tangent = _fallback_tangent(normal)

        vertices.extend(
            _pack_vertex(
                template=template,
                position=position,
                normal=normal,
                uv=(0.0, 0.0),
                tangent=tangent,
            )
        )

    indices = (
        np.asarray(
            mesh.faces,
            dtype=np.uint16,
        )
        .reshape(-1)
        .copy()
    )

    return (
        np.asarray(
            vertices,
            dtype=np.float32,
        ),
        indices,
    )


def _pack_vertex(
    *,
    template: Geometry,
    position,
    normal,
    uv,
    tangent,
) -> list[float]:
    values: list[float] = []

    for attr_name, size, _attr_type in template.fmt:
        if attr_name == b"v_pos":
            source = position
        elif attr_name == b"v_normal":
            source = normal
        elif attr_name == b"v_uv":
            source = uv
        elif attr_name == b"v_tangent":
            source = tangent
        else:
            source = [0.0] * size

        for index in range(size):
            if index < len(source):
                values.append(float(source[index]))
            else:
                values.append(0.0)

    return values


def _fallback_tangent(
    normal,
) -> tuple[float, float, float, float]:
    nx = float(normal[0])
    ny = float(normal[1])
    nz = float(normal[2])

    if abs(ny) < 0.999:
        up = np.array(
            [0.0, 1.0, 0.0],
            dtype=np.float64,
        )
    else:
        up = np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float64,
        )

    normal_vec = np.array(
        [nx, ny, nz],
        dtype=np.float64,
    )

    tangent = np.cross(
        up,
        normal_vec,
    )

    length = np.linalg.norm(tangent)

    if length <= 1e-12:
        return 1.0, 0.0, 0.0, 1.0

    tangent = tangent / length

    return (
        float(tangent[0]),
        float(tangent[1]),
        float(tangent[2]),
        1.0,
    )


def _transform_geometry(
    geometry: Geometry,
    matrix: Matrix4,
) -> Geometry:
    _validate_geometry(geometry)

    data = (
        np.asarray(
            geometry.vertices,
            dtype=np.float64,
        )
        .reshape((-1, geometry.stride))
        .copy()
    )

    positions = data[:, 0:3]

    homogeneous = np.column_stack(
        [
            positions,
            np.ones(
                len(positions),
                dtype=np.float64,
            ),
        ]
    )

    transformed = homogeneous @ matrix.values.T

    w = transformed[:, 3:4]

    safe_w = np.where(
        np.abs(w) > 1e-12,
        w,
        1.0,
    )

    data[:, 0:3] = transformed[:, 0:3] / safe_w

    if _has_attribute(geometry, b"v_normal"):
        normal_offset = _attribute_offset(geometry, b"v_normal")

        try:
            normal_matrix = matrix.compute_normal_matrix().values.astype(
                np.float64
            )

            normals = data[:, normal_offset:normal_offset + 3]
            normals = normals @ normal_matrix.T

            lengths = np.linalg.norm(
                normals,
                axis=1,
                keepdims=True,
            )

            normals = np.divide(
                normals,
                np.where(lengths > 1e-12, lengths, 1.0),
            )

            data[:, normal_offset:normal_offset + 3] = normals
        except Exception:
            pass

    if _has_attribute(geometry, b"v_tangent"):
        tangent_offset = _attribute_offset(geometry, b"v_tangent")

        try:
            normal_matrix = matrix.compute_normal_matrix().values.astype(
                np.float64
            )

            tangents = data[:, tangent_offset:tangent_offset + 3]
            tangents = tangents @ normal_matrix.T

            lengths = np.linalg.norm(
                tangents,
                axis=1,
                keepdims=True,
            )

            tangents = np.divide(
                tangents,
                np.where(lengths > 1e-12, lengths, 1.0),
            )

            data[:, tangent_offset:tangent_offset + 3] = tangents
        except Exception:
            pass

    return Geometry(
        name=geometry.name,
        fmt=list(geometry.fmt),
        vertices=data.reshape(-1).astype(np.float32),
        indices=np.asarray(
            geometry.indices,
            dtype=geometry.indices.dtype,
        ).copy(),
        mode=geometry.mode,
        texture=geometry.texture,
        has_tangents=geometry.has_tangents,
    )


def _validate_geometry(
    geometry: Geometry,
) -> None:
    if geometry.mode != "triangles":
        raise ValueError(
            "BooleanModifier only supports triangle geometry."
        )

    if geometry.stride <= 0:
        raise ValueError(
            "Geometry stride must be greater than zero."
        )

    if len(geometry.vertices) == 0:
        raise ValueError(
            "BooleanModifier received empty geometry."
        )

    if len(geometry.vertices) % geometry.stride != 0:
        raise ValueError(
            f"Geometry vertices length must be divisible by stride "
            f"{geometry.stride}."
        )

    if len(geometry.indices) == 0:
        raise ValueError(
            "BooleanModifier received geometry with no indices."
        )

    if len(geometry.indices) % 3 != 0:
        raise ValueError(
            "Geometry indices must describe triangles."
        )

    vertex_count = len(geometry.vertices) // geometry.stride

    min_index = int(np.min(geometry.indices))
    max_index = int(np.max(geometry.indices))

    if min_index < 0:
        raise ValueError(
            "Geometry indices cannot contain negative values."
        )

    if max_index >= vertex_count:
        raise ValueError(
            f"Geometry index {max_index} is outside vertex count "
            f"{vertex_count}."
        )

    if not _has_attribute(geometry, b"v_pos"):
        raise ValueError(
            "Geometry must contain a v_pos attribute."
        )


def _validate_index_limit(
    indices: np.ndarray,
) -> None:
    if indices.size == 0:
        return

    max_index = int(np.max(indices))

    if max_index > MAX_MESH_INDEX:
        raise OverflowError(
            "Boolean result has more than 65,535 vertices. "
            "Reduce cutter segments, simplify the geometry, or split the "
            "result into multiple meshes."
        )


def _attribute_offset(
    geometry: Geometry,
    attr_name: bytes,
) -> int:
    offset = 0

    for name, size, _attr_type in geometry.fmt:
        if name == attr_name:
            return offset

        offset += size

    raise ValueError(
        f"Geometry does not contain attribute {attr_name!r}."
    )


def _has_attribute(
    geometry: Geometry,
    attr_name: bytes,
) -> bool:
    return any(
        name == attr_name
        for name, _size, _attr_type in geometry.fmt
    )


def _extract_geometry(
    value: GeometryLike,
) -> Geometry:
    if isinstance(value, Geometry):
        return value

    if isinstance(value, Object3D):
        return value.geometry

    raise TypeError(
        "Expected Geometry or Object3D."
    )


def _copy_geometry(
    geometry: Geometry,
) -> Geometry:
    return Geometry(
        name=geometry.name,
        fmt=list(geometry.fmt),
        vertices=geometry.vertices.copy(),
        indices=geometry.indices.copy(),
        mode=geometry.mode,
        texture=geometry.texture,
        has_tangents=geometry.has_tangents,
    )


__all__ = [
    "BooleanModifier",
    "BooleanModifierError",
    "BooleanOperation",
]
