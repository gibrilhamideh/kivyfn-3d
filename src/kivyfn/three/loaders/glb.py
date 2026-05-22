# kivyfn/three/loaders/glb.py

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import numpy as np
from pygltflib import GLTF2

from kivyfn.three.loaders.asset import AssetObject, SceneAsset
from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform
from kivyfn.three.math.vector import Vector3
from kivyfn.three.objects.geometry import Geometry


class GlbLoader:
    def __init__(
        self,
        flip_v: bool = True,
        flip_winding: bool = False,
    ):
        self.flip_v = flip_v
        self.flip_winding = flip_winding

        self.scene: SceneAsset = SceneAsset()
        self._gltf: Any = None
        self._buffer_bytes: bytes | None = None

    def load(
        self,
        filename: str | Path,
    ) -> SceneAsset:
        path = Path(filename)

        self.scene = SceneAsset()
        self._gltf = GLTF2().load_binary(str(path))
        self._buffer_bytes = self._load_buffer_bytes(path)

        node_world_matrices = self._build_node_world_matrices()

        for node_index, node in enumerate(self._gltf.nodes or []):
            if node.mesh is None:
                continue

            mesh_object = self._gltf.meshes[node.mesh]

            node_name = (
                node.name
                or mesh_object.name
                or f"mesh_{node.mesh}"
            )

            world_transform = self._transform_from_matrix4(
                node_world_matrices[node_index]
            )

            for primitive_index, primitive in enumerate(mesh_object.primitives or []):
                geometry = self._process_primitive(primitive)

                if geometry is None:
                    continue

                key = (
                    node_name
                    if len(mesh_object.primitives) == 1
                    else f"{node_name}.{primitive_index:03d}"
                )

                geometry.name = key

                self.scene.objects[key] = AssetObject(
                    name=key,
                    geometry=geometry,
                    transform=world_transform.copy(),
                    material=None,
                )

        return self.scene

    # =================================== #
    # Node Transforms
    # =================================== #
    def _build_node_world_matrices(self) -> list[Matrix4]:
        nodes = self._gltf.nodes or []

        node_local_matrices = [
            self._get_node_local_matrix(node)
            for node in nodes
        ]

        node_world_matrices = [
            Matrix4.identity()
            for _ in nodes
        ]

        visited: set[int] = set()

        def walk(
            node_index: int,
            parent_matrix: Matrix4,
        ) -> None:
            if node_index in visited:
                return

            visited.add(node_index)

            world_matrix = parent_matrix @ node_local_matrices[node_index]
            node_world_matrices[node_index] = world_matrix

            node = nodes[node_index]

            for child_index in node.children or []:
                walk(
                    child_index,
                    world_matrix,
                )

        if self._gltf.scenes and self._gltf.scene is not None:
            scene = self._gltf.scenes[self._gltf.scene]

            for root_index in scene.nodes or []:
                walk(
                    root_index,
                    Matrix4.identity(),
                )
        else:
            for node_index in range(len(nodes)):
                walk(
                    node_index,
                    Matrix4.identity(),
                )

        return node_world_matrices

    def _get_node_local_matrix(
        self,
        node: Any,
    ) -> Matrix4:
        if getattr(node, "matrix", None):
            return Matrix4(
                np.array(
                    node.matrix,
                    dtype=np.float32,
                ).reshape((4, 4))
            )

        translation_data = getattr(node, "translation", None)
        rotation_data = getattr(node, "rotation", None)
        scale_data = getattr(node, "scale", None)

        translation = (
            Vector3(
                float(translation_data[0]),
                float(translation_data[1]),
                float(translation_data[2]),
            )
            if translation_data is not None
            else Vector3(0.0, 0.0, 0.0)
        )

        rotation = (
            Quaternion(
                float(rotation_data[0]),
                float(rotation_data[1]),
                float(rotation_data[2]),
                float(rotation_data[3]),
            )
            if rotation_data is not None
            else Quaternion.identity()
        )

        scale = (
            Vector3(
                float(scale_data[0]),
                float(scale_data[1]),
                float(scale_data[2]),
            )
            if scale_data is not None
            else Vector3(1.0, 1.0, 1.0)
        )

        return Transform(
            translation=translation,
            rotation=rotation,
            scale=scale,
        ).to_matrix4()

    def _transform_from_matrix4(
        self,
        matrix: Matrix4,
    ) -> Transform:
        values = matrix.values

        translation = Vector3(
            float(values[0, 3]),
            float(values[1, 3]),
            float(values[2, 3]),
        )

        scale = Vector3(
            float(np.linalg.norm(values[:3, 0])),
            float(np.linalg.norm(values[:3, 1])),
            float(np.linalg.norm(values[:3, 2])),
        )

        rotation_values = values[:3, :3].copy()

        if scale.x != 0.0:
            rotation_values[:, 0] /= scale.x

        if scale.y != 0.0:
            rotation_values[:, 1] /= scale.y

        if scale.z != 0.0:
            rotation_values[:, 2] /= scale.z

        rotation = Quaternion.from_matrix3(
            Matrix3(rotation_values.astype(np.float32))
        )

        return Transform(
            translation=translation,
            rotation=rotation,
            scale=scale,
        )

    # =================================== #
    # Buffer Reading
    # =================================== #
    def _load_buffer_bytes(
        self,
        filename: Path,
    ) -> bytes:
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

    def _read_accessor(
        self,
        accessor_index: int | None,
    ):
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
            output = np.empty(
                (count, component_count),
                dtype=dtype,
            )

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

    # =================================== #
    # Geometry
    # =================================== #
    def _process_primitive(
        self,
        primitive: Any,
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

        positions = positions.astype(np.float32)

        if normals is None or normals.shape[1] < 3:
            normals = np.zeros_like(
                positions,
                dtype=np.float32,
            )
        else:
            normals = normals.astype(np.float32)

        if uvs is None or uvs.shape[1] < 2:
            uvs = np.zeros(
                (positions.shape[0], 2),
                dtype=np.float32,
            )
        else:
            uvs = uvs.astype(np.float32).copy()

        if self.flip_v:
            uvs[:, 1] = 1.0 - uvs[:, 1]

        final_indices = indices.reshape(-1).astype(np.int64)

        if self.flip_winding and len(final_indices) % 3 == 0:
            final_indices = final_indices.reshape(-1, 3)
            final_indices[:, [1, 2]] = final_indices[:, [2, 1]]
            final_indices = final_indices.reshape(-1)

        final_indices = self._ensure_uint16_indices(final_indices)

        packed_vertices = np.column_stack(
            [
                positions,
                normals,
                uvs,
            ]
        ).astype(np.float32).reshape(-1)

        return Geometry(
            vertices=packed_vertices.astype(float).tolist(),
            indices=final_indices.tolist(),
        )

    def _ensure_uint16_indices(
        self,
        indices,
    ):
        if int(indices.max()) > 65535:
            raise OverflowError(
                "Indices exceed 65535 in a single primitive."
            )

        return indices




