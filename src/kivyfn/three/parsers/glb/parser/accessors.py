# kivyfn/three/parsers/glb/parser/accessors.py

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.parsers.glb.parser.context import GlbContext


class GlbAccessor:
    dtype_map: ClassVar[dict[int, Any]] = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }

    component_count_map: ClassVar[dict[str, int]] = {
        "SCALAR": 1,
        "VEC2": 2,
        "VEC3": 3,
        "VEC4": 4,
        "MAT2": 4,
        "MAT3": 9,
        "MAT4": 16,
    }

    def __init__(
        self,
        context: GlbContext,
    ) -> None:
        self.context = context

    def read(
        self,
        index: int | None,
    ) -> np.ndarray | None:
        if index is None:
            return None

        gltf = self.context.gltf
        buffer_bytes = self.context.buffer_bytes

        accessor = gltf.accessors[index]

        if accessor.bufferView is None:
            return None

        view = gltf.bufferViews[accessor.bufferView]

        view_offset = view.byteOffset or 0
        accessor_offset = accessor.byteOffset or 0
        stride = view.byteStride or 0
        count = accessor.count

        dtype = self.dtype(accessor.componentType)
        component_count = self.component_count(accessor.type)

        dtype_info = np.dtype(dtype)
        element_size = dtype_info.itemsize * component_count
        start = view_offset + accessor_offset

        if stride and stride != element_size:
            return np.ndarray(
                shape=(count, component_count),
                dtype=dtype,
                buffer=buffer_bytes,
                offset=start,
                strides=(
                    stride,
                    dtype_info.itemsize,
                ),
            )

        array = np.frombuffer(
            buffer_bytes,
            dtype=dtype,
            count=count * component_count,
            offset=start,
        )

        return array.reshape((count, component_count))

    def bytes(
        self,
        index: int,
    ) -> bytes:
        gltf = self.context.gltf
        view = gltf.bufferViews[index]

        byte_offset = view.byteOffset or 0
        byte_length = view.byteLength or 0

        return self.context.buffer_bytes[
            byte_offset : byte_offset + byte_length
        ]

    def matrix(
        self,
        values: np.ndarray | list[float],
    ) -> Matrix4:
        return Matrix4(
            np.array(
                values,
                dtype=np.float32,
            ).reshape((4, 4)).T
        )

    def dtype(
        self,
        value: int,
    ) -> Any:
        try:
            return self.dtype_map[value]

        except KeyError:
            raise ValueError(
                f"Unsupported GLB accessor component type: {value!r}"
            ) from None

    def component_count(
        self,
        value: str,
    ) -> int:
        return self.component_count_map.get(
            value,
            1,
        )


__all__ = (
    "GlbAccessor",
)
