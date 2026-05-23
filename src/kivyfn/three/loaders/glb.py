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

        for root_index in self._get_scene_root_indices():
            root_asset = self._load_node(root_index)
            self.scene.tree.append(root_asset)

        return self.scene

    # =================================== #
    # Scene / Node Tree
    # =================================== #
    def _get_scene_root_indices(self) -> list[int]:
        if self._gltf.scenes and self._gltf.scene is not None:
            scene = self._gltf.scenes[self._gltf.scene]
            return list(scene.nodes or [])

        nodes = self._gltf.nodes or []
        child_indices: set[int] = set()

        for node in nodes:
            child_indices.update(node.children or [])

        return [
            index
            for index in range(len(nodes))
            if index not in child_indices
        ]

    def _load_node(
        self,
        node_index: int,
    ) -> AssetObject:
        node = self._gltf.nodes[node_index]

        node_name = self._get_node_name(
            node_index=node_index,
            node=node,
        )

        primitives = self._get_node_primitives(node)

        if len(primitives) == 1:
            geometry = self._process_primitive(primitives[0])

            if geometry is not None:
                geometry.name = node_name

            asset = AssetObject(
                name=node_name,
                geometry=geometry,
                transform=self._get_node_local_transform(node),
                material=None,
            )

            self._register_asset(asset)

        else:
            asset = AssetObject(
                name=node_name,
                geometry=None,
                transform=self._get_node_local_transform(node),
                material=None,
            )

            self._register_asset(asset)

            for primitive_index, primitive in enumerate(primitives):
                geometry = self._process_primitive(primitive)

                if geometry is None:
                    continue

                primitive_name = self._make_unique_name(
                    f"{node_name}.{primitive_index:03d}"
                )

                geometry.name = primitive_name

                primitive_asset = AssetObject(
                    name=primitive_name,
                    geometry=geometry,
                    transform=Transform(),
                    material=None,
                )

                self._register_asset(primitive_asset)
                asset.children.append(primitive_asset)

        for child_index in node.children or []:
            child_asset = self._load_node(child_index)
            asset.children.append(child_asset)

        return asset

    def _get_node_name(
        self,
        node_index: int,
        node: Any,
    ) -> str:
        mesh_name = None

        if node.mesh is not None:
            mesh = self._gltf.meshes[node.mesh]
            mesh_name = mesh.name

        name = (
            node.name
            or mesh_name
            or f"node_{node_index}"
        )

        return self._make_unique_name(name)

    def _make_unique_name(
        self,
        name: str,
    ) -> str:
        if name not in self.scene.objects:
            return name

        counter = 1

        while True:
            candidate = f"{name}.{counter:03d}"

            if candidate not in self.scene.objects:
                return candidate

            counter += 1

    def _register_asset(
        self,
        asset: AssetObject,
    ) -> None:
        self.scene.objects[asset.name] = asset

    def _get_node_primitives(
        self,
        node: Any,
    ) -> list[Any]:
        if node.mesh is None:
            return []

        mesh = self._gltf.meshes[node.mesh]
        return list(mesh.primitives or [])

    # =================================== #
    # Node Transforms
    # =================================== #
    def _get_node_local_transform(
        self,
        node: Any,
    ) -> Transform:
        return self._transform_from_matrix4(
            self._get_node_local_matrix(node)
        )

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




