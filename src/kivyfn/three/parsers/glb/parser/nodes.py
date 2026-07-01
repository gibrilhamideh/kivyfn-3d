# kivyfn/three/parsers/glb/parser/nodes.py

from __future__ import annotations

import numpy as np

from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform
from kivyfn.three.math.vector import Vector3
from kivyfn.three.parsers.glb.node import GlbNode
from kivyfn.three.parsers.glb.primitive import GlbPrimitive
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import (
    GlbMeshData,
    GlbNodeData,
    GlbPrimitiveData,
)
from kivyfn.three.parsers.glb.parser.geometry import GlbGeometry
from kivyfn.three.parsers.glb.parser.materials import GlbMaterials
from kivyfn.three.parsers.glb.parser.registry import GlbRegistry


class GlbNodes:
    def __init__(
        self,
        context: GlbContext,
        accessor: GlbAccessor,
        registry: GlbRegistry,
        geometry: GlbGeometry,
        materials: GlbMaterials,
    ) -> None:
        self.context = context
        self.accessor = accessor
        self.registry = registry
        self.geometry = geometry
        self.materials = materials

    def load(
        self,
        index: int,
    ) -> GlbNode:
        data = GlbNodeData(
            self.context.gltf.nodes[index],
        )

        name = self.registry.name(
            index=index,
            data=data,
        )

        node = GlbNode(
            name=name,
            gltf_index=index,
            transform=self.local_transform(data),
            extras=data.extras.copy(),
            skin_index=data.skin_index,
            morph_weights=self.weights(data),
        )

        self.registry.register(node)

        for primitive_index, primitive in enumerate(
            self.primitives(data),
        ):
            primitive_name = name

            if len(self.primitives(data)) > 1:
                primitive_name = self.registry.unique(
                    f"{name}.{primitive_index:03d}",
                )

            geometry = self.geometry.load(
                primitive,
            )

            if geometry is None:
                continue

            geometry.name = primitive_name

            material = self.materials.load(
                primitive=primitive,
                fallback_name=primitive_name,
            )

            node.primitives.append(
                GlbPrimitive(
                    name=primitive_name,
                    geometry=geometry,
                    material=material,
                    extras=primitive.extras.copy(),
                )
            )

        for child_index in data.children:
            child = self.cached(child_index)
            child.parent = node
            node.children.append(
                self.cached(child_index),
            )

        return node

    def cached(
        self,
        index: int,
    ) -> GlbNode:
        existing = self.registry.node(index)

        if existing is not None:
            return existing

        return self.load(index)

    def primitives(
        self,
        data: GlbNodeData,
    ) -> list[GlbPrimitiveData]:
        if data.mesh_index is None:
            return []

        mesh = GlbMeshData(
            self.context.gltf.meshes[data.mesh_index],
        )

        return [
            GlbPrimitiveData(raw_primitive)
            for raw_primitive in mesh.primitives
        ]

    def weights(
        self,
        data: GlbNodeData,
    ) -> tuple[float, ...]:
        if data.mesh_index is None:
            return ()

        mesh = GlbMeshData(
            self.context.gltf.meshes[data.mesh_index],
        )

        return mesh.weights

    def local_transform(
        self,
        data: GlbNodeData,
    ) -> Transform:
        if data.matrix:
            return self.from_matrix(
                self.accessor.matrix(data.matrix),
            )

        return self.from_components(data)

    def from_components(
        self,
        data: GlbNodeData,
    ) -> Transform:
        translation_data = data.translation
        rotation_data = data.rotation
        scale_data = data.scale

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
        )

    def from_matrix(
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
            Matrix3(
                rotation_values.astype(
                    np.float32,
                    copy=False,
                )
            )
        )

        return Transform(
            translation=translation,
            rotation=rotation,
            scale=scale,
        )


__all__ = (
    "GlbNodes",
)
