# kivyfn/three/parsers/glb/parser/registry.py

from __future__ import annotations

from kivyfn.three.parsers.glb.node import GlbNode
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import GlbNodeData


class GlbRegistry:
    def __init__(
        self,
        context: GlbContext,
    ) -> None:
        self.context = context

    def node(
        self,
        index: int,
    ) -> GlbNode | None:
        return self.context.blueprint.nodes_by_index.get(index)

    def name(
        self,
        index: int,
        data: GlbNodeData,
    ) -> str:
        mesh_name = None

        if data.mesh_index is not None:
            mesh = self.context.gltf.meshes[data.mesh_index]
            mesh_name = getattr(mesh, "name", None)

        value = (
            data.name
            or mesh_name
            or f"node_{index}"
        )

        return self.unique(value)

    def unique(
        self,
        name: str,
    ) -> str:
        blueprint = self.context.blueprint

        if name not in blueprint.nodes_by_name:
            return name

        counter = 1

        while True:
            candidate = f"{name}.{counter:03d}"

            if candidate not in blueprint.nodes_by_name:
                return candidate

            counter += 1

    def register(
        self,
        node: GlbNode,
    ) -> None:
        blueprint = self.context.blueprint

        if node.gltf_index in blueprint.nodes_by_index:
            raise ValueError(
                f"Duplicate GLB node index: {node.gltf_index!r}"
            )

        if node.name in blueprint.nodes_by_name:
            raise ValueError(
                f"Duplicate GLB node name: {node.name!r}"
            )

        blueprint.nodes_by_index[node.gltf_index] = node
        blueprint.nodes_by_name[node.name] = node


__all__ = (
    "GlbRegistry",
)
