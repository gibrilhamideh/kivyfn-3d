# kivyfn/three/parsers/glb/parser/skins.py

from __future__ import annotations

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import GlbSkinData
from kivyfn.three.parsers.glb.skin import GlbSkin


class GlbSkins:
    def __init__(
        self,
        context: GlbContext,
        accessor: GlbAccessor,
    ) -> None:
        self.context = context
        self.accessor = accessor

    def load(
        self,
    ) -> list[GlbSkin]:
        gltf = self.context.gltf
        raw_skins = list(gltf.skins or [])

        if not raw_skins:
            return []

        skins: list[GlbSkin] = []

        for index, raw_skin in enumerate(raw_skins):
            data = GlbSkinData(
                raw_skin,
            )

            if not data.joints:
                raise ValueError(
                    f"GLB skin {index} has no joints."
                )

            skins.append(
                GlbSkin(
                    name=(
                        data.name
                        or f"skin_{index}"
                    ),
                    joint_indices=tuple(data.joints),
                    inverse_bind_matrices=tuple(
                        self.inverse_bind_matrices(
                            data=data,
                            index=index,
                        )
                    ),
                )
            )

        return skins

    def inverse_bind_matrices(
        self,
        *,
        data: GlbSkinData,
        index: int,
    ) -> list[Matrix4]:
        accessor_index = data.inverse_bind_matrices_index

        if accessor_index is None:
            return [
                Matrix4.identity()
                for _ in data.joints
            ]

        values = self.accessor.read(
            accessor_index,
        )

        if values is None:
            raise ValueError(
                f"GLB skin {index} has invalid inverseBindMatrices."
            )

        if len(values) != len(data.joints):
            raise ValueError(
                f"GLB skin {index} inverseBindMatrices count does not "
                f"match joint count: {len(values)} != {len(data.joints)}."
            )

        return [
            self.accessor.matrix(row)
            for row in values
        ]

    def validate(
        self,
    ) -> None:
        skin_count = len(
            self.context.blueprint.skins,
        )

        for node in self.context.blueprint.nodes_by_index.values():
            if node.skin_index is None:
                continue

            if node.skin_index < 0 or node.skin_index >= skin_count:
                raise ValueError(
                    f"GLB node {node.name!r} references invalid skin index "
                    f"{node.skin_index!r}."
                )



