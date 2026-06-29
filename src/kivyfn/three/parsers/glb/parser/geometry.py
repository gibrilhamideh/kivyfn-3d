# kivyfn/three/parsers/glb/parser/geometry.py

from __future__ import annotations

from typing import ClassVar

import numpy as np

from kivyfn.three.types import MeshMode
from kivyfn.three.assets.geometry import (
    Geometry,
    GeometryBounds,
    MorphTarget,
)
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.data import (
    GlbMorphTargetData,
    GlbPrimitiveData,
)


class GlbGeometry:
    mode_map: ClassVar[dict[int, MeshMode]] = {
        0: "points",
        1: "lines",
        2: "line_loop",
        3: "line_strip",
        4: "triangles",
        5: "triangle_strip",
        6: "triangle_fan",
    }

    def __init__(
        self,
        context: GlbContext,
        accessor: GlbAccessor,
    ) -> None:
        self.context = context
        self.accessor = accessor

    def load(
        self,
        primitive: GlbPrimitiveData,
    ) -> Geometry | None:
        if primitive.position_index is None:
            return None

        mode = self.mode(primitive.mode)

        positions = self.positions(
            primitive,
        )

        if positions is None:
            return None

        vertex_count = positions.shape[0]

        indices = self.indices(
            primitive=primitive,
            vertex_count=vertex_count,
        )

        if indices is None:
            return None

        normals = self.normals(
            primitive=primitive,
            positions=positions,
        )

        uvs = self.uvs(
            primitive=primitive,
            vertex_count=vertex_count,
        )

        columns: list[np.ndarray] = [
            positions,
            normals,
            uvs,
        ]

        fmt: list[tuple[bytes, int, str]] = [
            (b"v_pos", 3, "float"),
            (b"v_normal", 3, "float"),
            (b"v_uv", 2, "float"),
        ]

        has_tangents = self.tangents(
            primitive=primitive,
            columns=columns,
            fmt=fmt,
        )

        has_colors = False
        # has_colors = self.colors(
        #     primitive=primitive,
        #     vertex_count=vertex_count,
        #     columns=columns,
        #     fmt=fmt,
        # )

        has_skin = self.skin(
            primitive=primitive,
            columns=columns,
            fmt=fmt,
        )

        vertices = np.column_stack(
            columns,
        ).reshape(-1)

        morph_targets = self.morphs(
            primitive,
        )

        indices = self.winding(
            indices,
        )

        indices = self.uint16(
            indices,
        )

        return Geometry(
            fmt=fmt,
            vertices=vertices,
            indices=indices,
            bounds=GeometryBounds.from_positions(
                positions,
            ),
            mode=mode,
            has_tangents=has_tangents,
            has_skin=has_skin,
            has_colors=has_colors,
            morph_targets=tuple(morph_targets),
        )

    def mode(
        self,
        value: int,
    ) -> MeshMode:
        return self.mode_map.get(
            value,
            "triangles",
        )

    def positions(
        self,
        primitive: GlbPrimitiveData,
    ) -> np.ndarray | None:
        positions = self.accessor.read(
            primitive.position_index,
        )

        if positions is None:
            return None

        if positions.shape[1] < 3:
            return None

        return positions[:, :3].astype(
            np.float32,
            copy=False,
        )

    def indices(
        self,
        *,
        primitive: GlbPrimitiveData,
        vertex_count: int,
    ) -> np.ndarray | None:
        if primitive.indices_index is None:
            return np.arange(
                vertex_count,
                dtype=np.int64,
            )

        indices = self.accessor.read(
            primitive.indices_index,
        )

        if indices is None:
            return None

        return indices.reshape(-1).astype(
            np.int64,
            copy=False,
        )

    def normals(
        self,
        *,
        primitive: GlbPrimitiveData,
        positions: np.ndarray,
    ) -> np.ndarray:
        normals = self.accessor.read(
            primitive.normal_index,
        )

        if normals is None or normals.shape[1] < 3:
            return np.zeros_like(
                positions,
                dtype=np.float32,
            )

        return normals[:, :3].astype(
            np.float32,
            copy=False,
        )

    def uvs(
        self,
        *,
        primitive: GlbPrimitiveData,
        vertex_count: int,
    ) -> np.ndarray:
        uvs = self.accessor.read(
            primitive.uv_index,
        )

        if uvs is None or uvs.shape[1] < 2:
            result = np.zeros(
                (vertex_count, 2),
                dtype=np.float32,
            )

        else:
            result = uvs[:, :2].astype(
                np.float32,
                copy=False,
            )

            if self.context.options.flip_v:
                result = result.copy()

        if self.context.options.flip_v:
            result[:, 1] = 1.0 - result[:, 1]

        return result

    def tangents(
        self,
        *,
        primitive: GlbPrimitiveData,
        columns: list[np.ndarray],
        fmt: list[tuple[bytes, int, str]],
    ) -> bool:
        tangents = self.accessor.read(
            primitive.tangent_index,
        )

        if tangents is None or tangents.shape[1] < 4:
            return False

        columns.append(
            tangents[:, :4].astype(
                np.float32,
                copy=False,
            )
        )

        fmt.append(
            (b"v_tangent", 4, "float"),
        )

        return True

    def colors(
        self,
        *,
        primitive: GlbPrimitiveData,
        vertex_count: int,
        columns: list[np.ndarray],
        fmt: list[tuple[bytes, int, str]],
    ) -> bool:
        colors = self.accessor.read(
            primitive.color_index,
        )

        if colors is None or colors.shape[1] < 3:
            return False

        if colors.shape[1] >= 4:
            final_colors = colors[:, :4].astype(
                np.float32,
                copy=False,
            )

        else:
            rgb = colors[:, :3].astype(
                np.float32,
                copy=False,
            )

            alpha = np.ones(
                (vertex_count, 1),
                dtype=np.float32,
            )

            final_colors = np.column_stack(
                [
                    rgb,
                    alpha,
                ]
            )

        columns.append(
            final_colors,
        )

        fmt.append(
            (b"v_color", 4, "float"),
        )

        return True

    def skin(
        self,
        *,
        primitive: GlbPrimitiveData,
        columns: list[np.ndarray],
        fmt: list[tuple[bytes, int, str]],
    ) -> bool:
        joints = self.accessor.read(
            primitive.joints_index,
        )

        weights = self.accessor.read(
            primitive.weights_index,
        )

        has_joints = (
            joints is not None
            and joints.shape[1] >= 4
        )

        has_weights = (
            weights is not None
            and weights.shape[1] >= 4
        )

        if not has_joints or not has_weights:
            return False

        assert joints is not None
        assert weights is not None

        columns.append(
            joints[:, :4].astype(
                np.float32,
                copy=False,
            )
        )

        columns.append(
            weights[:, :4].astype(
                np.float32,
                copy=False,
            )
        )

        fmt.append(
            (b"v_joints", 4, "float"),
        )

        fmt.append(
            (b"v_weights", 4, "float"),
        )

        return True

    def morphs(
        self,
        primitive: GlbPrimitiveData,
    ) -> list[MorphTarget]:
        targets: list[MorphTarget] = []

        for raw_target in primitive.targets:
            target = GlbMorphTargetData(
                raw_target,
            )

            positions = self.morph_values(
                target.position_index,
            )

            normals = self.morph_values(
                target.normal_index,
            )

            tangents = self.morph_values(
                target.tangent_index,
            )

            targets.append(
                MorphTarget(
                    positions=positions,
                    normals=normals,
                    tangents=tangents,
                )
            )

        return targets

    def morph_values(
        self,
        index: int | None,
    ) -> np.ndarray | None:
        values = self.accessor.read(
            index,
        )

        if values is None:
            return None

        if values.shape[1] < 3:
            return None

        return values[:, :3].astype(
            np.float32,
            copy=False,
        )

    def winding(
        self,
        indices: np.ndarray,
    ) -> np.ndarray:
        if not self.context.options.flip_winding:
            return indices

        if len(indices) % 3 != 0:
            return indices

        result = indices.reshape(-1, 3).copy()
        result[:, [1, 2]] = result[:, [2, 1]]

        return result.reshape(-1)

    def uint16(
        self,
        indices: np.ndarray,
    ) -> np.ndarray:
        if indices.size == 0:
            return indices.astype(
                np.uint16,
                copy=False,
            )

        total = int(
            indices.max(),
        )

        if total > 65535:
            raise OverflowError(
                "Indices exceed 65535 in a single primitive. "
                "Split the primitive before loading it."
            )

        return indices.astype(
            np.uint16,
            copy=False,
        )


__all__ = (
    "GlbGeometry",
)
