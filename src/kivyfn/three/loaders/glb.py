# kivyfn/three/loaders/glb.py

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import numpy as np
from pygltflib import GLTF2

from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform
from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.render.geometry import Geometry


class GlbLoader:
    def __init__(
        self,
        flip_v: bool = True,
        flip_winding: bool = False,
    ):
        self.flip_v = flip_v
        self.flip_winding = flip_winding

        self.objects: dict[str, Geometry] = {}
        self._gltf: Any = None
        self._buffer_bytes: bytes | None = None

    def load(self, filename: str | Path) -> dict[str, Geometry]:
        path = Path(filename)

        self.objects = {}
        self._gltf = GLTF2().load_binary(str(path))
        self._buffer_bytes = self._load_buffer_bytes(path)

        node_world = self._build_node_world_matrices()

        for node_index, node in enumerate(self._gltf.nodes or []):
            if node.mesh is None:
                continue

            world_matrix = node_world[node_index]
            normal_matrix = world_matrix.compute_normal_matrix()

            mesh_object = self._gltf.meshes[node.mesh]
            node_name = node.name or mesh_object.name or f"mesh_{node.mesh}"

            for primitive_index, primitive in enumerate(mesh_object.primitives or []):
                geometry = self._process_primitive(
                    primitive=primitive,
                    world_matrix=world_matrix,
                    normal_matrix=normal_matrix,
                )

                if geometry is None:
                    continue

                key = (
                    node_name
                    if len(mesh_object.primitives) == 1
                    else f"{node_name}.{primitive_index:03d}"
                )

                geometry.name = key
                self.objects[key] = geometry

        return self.objects

    def _load_buffer_bytes(self, filename: Path) -> bytes:
        buffer_bytes = self._gltf.binary_blob()

        if buffer_bytes is not None:
            return buffer_bytes

        if not self._gltf.buffers:
            raise ValueError("No buffer found in GLB file.")

        uri = self._gltf.buffers[0].uri

        if uri and uri.startswith("data:"):
            encoded = uri.split(",", 1)[1]
            return base64.b64decode(encoded)

        if uri:
            bin_path = uri if os.path.isabs(uri) else filename.parent / uri

            with open(bin_path, "rb") as file:
                return file.read()

        raise ValueError("No binary buffer found in GLB file.")

    def _read_accessor(self, accessor_index: int | None):
        if accessor_index is None:
            return None

        if self._buffer_bytes is None:
            raise RuntimeError("GLB buffer bytes were not loaded.")

        buffer_bytes = self._buffer_bytes

        accessor = self._gltf.accessors[accessor_index]

        if accessor.bufferView is None:
            return None

        view = self._gltf.bufferViews[accessor.bufferView]

        view_offset = view.byteOffset or 0
        accessor_offset = accessor.byteOffset or 0
        stride = view.byteStride or 0
        count = accessor.count

        dtype_map = {
            5120: np.int8,
            5121: np.uint8,
            5122: np.int16,
            5123: np.uint16,
            5125: np.uint32,
            5126: np.float32,
        }

        component_count_map = {
            "SCALAR": 1,
            "VEC2": 2,
            "VEC3": 3,
            "VEC4": 4,
            "MAT2": 4,
            "MAT3": 9,
            "MAT4": 16,
        }

        dtype = dtype_map[accessor.componentType]
        component_count = component_count_map.get(accessor.type, 1)

        element_size = np.dtype(dtype).itemsize * component_count
        start = view_offset + accessor_offset

        if stride and stride != element_size:
            output = np.empty((count, component_count), dtype=dtype)
            position = start

            for index in range(count):
                output[index, :] = np.frombuffer(
                    buffer_bytes,
                    dtype=dtype,
                    count=component_count,
                    offset=position,
                )

                position += stride

            return output

        array = np.frombuffer(
            buffer_bytes,
            dtype=dtype,
            count=count * component_count,
            offset=start,
        )

        return array.reshape((count, component_count))

    def _build_node_world_matrices(self) -> list[Matrix4]:
        node_world = [
            Matrix4.identity()
            for _ in (self._gltf.nodes or [])
        ]

        node_local: list[Matrix4] = []

        for node in self._gltf.nodes or []:
            if getattr(node, "matrix", None):
                matrix = Matrix4(
                    np.array(node.matrix, dtype=np.float32).reshape((4, 4))
                )
            else:
                scale = getattr(node, "scale", None)
                translation = getattr(node, "translation", None)
                rotation = getattr(node, "rotation", None)
                rotation=(
                        Quaternion(*rotation)
                        if rotation is not None
                        else Quaternion.identity()
                    )

                matrix = Transform(
                    translation=translation,
                    rotation=rotation,
                    scale=scale,
                ).to_matrix4()            

                node_local.append(matrix)

        def walk(node_index: int, parent_matrix: Matrix4) -> None:
            world_matrix = parent_matrix @ node_local[node_index]
            node_world[node_index] = world_matrix

            for child_index in self._gltf.nodes[node_index].children or []:
                walk(child_index, world_matrix)

        if self._gltf.scenes and self._gltf.scene is not None:
            scene = self._gltf.scenes[self._gltf.scene]

            for root_index in scene.nodes or []:
                walk(root_index, Matrix4.identity())
        else:
            for node_index in range(len(self._gltf.nodes or [])):
                walk(node_index, Matrix4.identity())

        return node_world

    def _process_primitive(
        self,
        primitive: Any,
        world_matrix: Matrix4,
        normal_matrix: Matrix3,
    ) -> Geometry | None:
        position_index = getattr(primitive.attributes, "POSITION", None)
        normal_index = getattr(primitive.attributes, "NORMAL", None)
        uv_index = getattr(primitive.attributes, "TEXCOORD_0", None)
        index_index = primitive.indices

        if position_index is None or index_index is None:
            return None

        positions = self._read_accessor(position_index)
        normals = self._read_accessor(normal_index)
        uvs = self._read_accessor(uv_index)
        indices = self._read_accessor(index_index)

        if positions is None or indices is None:
            return None

        if normals is None or normals.shape[1] < 3:
            normals = np.zeros_like(positions, dtype=np.float32)

        if uvs is None or uvs.shape[1] < 2:
            uvs = np.zeros((positions.shape[0], 2), dtype=np.float32)

        transformed_positions = self._transform_positions(
            positions=positions,
            world_matrix=world_matrix,
        )

        transformed_normals = self._transform_normals(
            normals=normals,
            normal_matrix=normal_matrix,
        )

        if self.flip_v:
            uvs = uvs.astype(np.float32).copy()
            uvs[:, 1] = 1.0 - uvs[:, 1]

        final_indices = indices.reshape(-1).astype(np.int64)

        if self.flip_winding and len(final_indices) % 3 == 0:
            final_indices = final_indices.reshape(-1, 3)
            final_indices[:, [1, 2]] = final_indices[:, [2, 1]]
            final_indices = final_indices.reshape(-1)

        final_indices = self._ensure_uint16_indices(final_indices)

        packed_vertices = np.column_stack(
            [
                transformed_positions,
                transformed_normals,
                uvs,
            ]
        ).astype(np.float32).reshape(-1)


        vertices = packed_vertices.astype(float).tolist()
        indices = final_indices.tolist()
        return Geometry(vertices=vertices, indices=indices)


    def _transform_positions(
        self,
        positions,
        world_matrix: Matrix4,
    ):
        homogeneous_positions = np.concatenate(
            [
                positions.astype(np.float32),
                np.ones((positions.shape[0], 1), dtype=np.float32),
            ],
            axis=1,
        )

        return (homogeneous_positions @ world_matrix.values.T)[:, :3]

    def _transform_normals(
        self,
        normals,
        normal_matrix: Matrix3,
    ):
        transformed_normals = normals.astype(np.float32) @ normal_matrix.values.T

        lengths = (
            np.linalg.norm(
                transformed_normals,
                axis=1,
                keepdims=True,
            )
            + 1e-12
        )

        return transformed_normals / lengths

    def _ensure_uint16_indices(self, indices):
        if int(indices.max()) > 65535:
            raise OverflowError(
                "Indices exceed 65535 in a single primitive."
            )

        return indices




