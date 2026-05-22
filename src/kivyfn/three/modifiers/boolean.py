from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import numpy as np

from kivyfn.three.backends.trimesh import require_boolean_backend
from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.objects import Geometry, Material, Object3D


BooleanOperation = Literal[
    "difference",
    "union",
    "intersection",
]

BooleanEngine = Literal[
    "manifold",
    "blender"
]

GeometryLike = Geometry | Object3D

VERTEX_STRIDE = 8
MAX_MESH_INDEX = 65_535


class BooleanModifierError(RuntimeError):
    """Raised when a boolean modifier operation fails."""


class BooleanModifier:
    """
    Boolean geometry modifier.

    This modifier works in two modes:

    1. apply(geometry)
       Operates directly on raw Geometry objects.
       In this mode, all geometry must already be in the same coordinate space.

    2. apply_to_object(object3d)
       Operates on Object3D instances.
       Cutter objects are transformed into the base object's local space before
       running the boolean operation.

    Notes:
        - Input geometry must be triangle mesh geometry.
        - Input geometry should be watertight for Manifold booleans.
        - Generated UVs are currently reset to 0,0.
        - The output uses flat shading by default for cleaner hard edges.
    """

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

    # =================================== #
    # Public API
    # =================================== #
    def add_cutter(
        self,
        cutter: GeometryLike,
    ) -> None:
        self.cutters.append(cutter)

    def remove_cutter(
        self,
        cutter: GeometryLike,
    ) -> None:
        self.cutters.remove(cutter)

    def clear_cutters(self) -> None:
        self.cutters.clear()

    def apply(
        self,
        geometry: Geometry,
        *,
        cutters: Iterable[GeometryLike] | None = None,
    ) -> Geometry:
        """
        Apply the boolean operation to raw geometry.

        This assumes the base geometry and cutter geometry are already in the
        same coordinate space.
        """
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
        """
        Apply the boolean operation to an Object3D and return a new Object3D.

        Object3D cutters are converted into the base object's local space.
        This keeps the returned geometry local to the base object and preserves
        the base object's transform.
        """
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

    # =================================== #
    # Internal Operations
    # =================================== #
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

        # Convert cutter local geometry into base local space:
        #
        # cutter local -> world -> base local
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


# =================================== #
# Geometry Conversion
# =================================== #
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
    ).reshape((-1, VERTEX_STRIDE))

    vertices = vertex_data[:, 0:3].copy()

    faces = np.asarray(
        geometry.indices,
        dtype=np.int64,
    ).reshape((-1, 3))



    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=process,
    )

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
        return Geometry(
            name=name,
            fmt=list(template.fmt),
            vertices=[],
            indices=[],
            mode="triangles",
            texture=template.texture if keep_texture else None,
        )

    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()

    if flat_shading:
        vertices, indices = _build_flat_geometry_data(mesh)
    else:
        vertices, indices = _build_smooth_geometry_data(mesh)

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
) -> tuple[list[float], list[int]]:
    """
    Build geometry with duplicated vertices per triangle.

    This gives cleaner hard edges for boxes, walls, cutouts, and CAD-like
    dashboard geometry.
    """
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

        for source_index in face:
            position = positions[source_index]

            vertices.extend(
                [
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),

                    float(normal[0]),
                    float(normal[1]),
                    float(normal[2]),

                    0.0,
                    0.0,
                ]
            )

            indices.append(vertex_index)
            vertex_index += 1

    return vertices, indices


def _build_smooth_geometry_data(
    mesh,
) -> tuple[list[float], list[int]]:
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
        vertices.extend(
            [
                float(position[0]),
                float(position[1]),
                float(position[2]),

                float(normal[0]),
                float(normal[1]),
                float(normal[2]),

                0.0,
                0.0,
            ]
        )

    indices = (
        np.asarray(
            mesh.faces,
            dtype=np.int64,
        )
        .reshape(-1)
        .astype(int)
        .tolist()
    )

    return vertices, indices


# =================================== #
# Transform Helpers
# =================================== #
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
        .reshape((-1, VERTEX_STRIDE))
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

    # Normals do not affect the boolean operation itself, but keeping them
    # roughly correct makes this helper safer if reused elsewhere.
    try:
        normal_matrix = matrix.compute_normal_matrix().values.astype(np.float64)
        normals = data[:, 3:6] @ normal_matrix.T

        lengths = np.linalg.norm(
            normals,
            axis=1,
            keepdims=True,
        )

        normals = np.divide(
            normals,
            np.where(lengths > 1e-12, lengths, 1.0),
        )

        data[:, 3:6] = normals
    except Exception:
        pass

    return Geometry(
        name=geometry.name,
        fmt=list(geometry.fmt),
        vertices=data.reshape(-1).astype(float).tolist(),
        indices=list(geometry.indices),
        mode=geometry.mode,
        texture=geometry.texture,
    )


# =================================== #
# Validation Helpers
# =================================== #
def _validate_geometry(
    geometry: Geometry,
) -> None:
    if geometry.mode != "triangles":
        raise ValueError(
            "BooleanModifier only supports triangle geometry."
        )

    if len(geometry.vertices) == 0:
        raise ValueError(
            "BooleanModifier received empty geometry."
        )

    if len(geometry.vertices) % VERTEX_STRIDE != 0:
        raise ValueError(
            "Geometry vertices must use stride 8: "
            "x, y, z, nx, ny, nz, u, v."
        )

    if len(geometry.indices) == 0:
        raise ValueError(
            "BooleanModifier received geometry with no indices."
        )

    if len(geometry.indices) % 3 != 0:
        raise ValueError(
            "Geometry indices must describe triangles."
        )

    vertex_count = len(geometry.vertices) // VERTEX_STRIDE

    min_index = min(geometry.indices)
    max_index = max(geometry.indices)

    if min_index < 0:
        raise ValueError(
            "Geometry indices cannot contain negative values."
        )

    if max_index >= vertex_count:
        raise ValueError(
            f"Geometry index {max_index} is outside vertex count "
            f"{vertex_count}."
        )


def _validate_index_limit(
    indices: list[int],
) -> None:
    if not indices:
        return

    max_index = max(indices)

    if max_index > MAX_MESH_INDEX:
        raise OverflowError(
            "Boolean result has more than 65,535 vertices. "
            "Kivy Mesh indices are safest under this limit. "
            "Reduce cutter segments, simplify the geometry, or split the "
            "result into multiple meshes."
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
        vertices=list(geometry.vertices),
        indices=list(geometry.indices),
        mode=geometry.mode,
        texture=geometry.texture,
    )


__all__ = [
    "BooleanModifier",
    "BooleanModifierError",
    "BooleanOperation",
]
