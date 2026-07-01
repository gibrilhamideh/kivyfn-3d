# kivyfn/three/skinning/palette.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from kivyfn.three.skinning.skin import Skin

if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D


@dataclass(slots=True)
class SkinPalette:
    _array: np.ndarray | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _bytes: bytes = field(
        default=b"",
        init=False,
        repr=False,
    )

    _joint_count: int = field(
        default=0,
        init=False,
        repr=False,
    )

    @property
    def joint_count(
        self,
    ) -> int:
        return self._joint_count

    @property
    def bytes(
        self,
    ) -> bytes:
        return self._bytes

    @property
    def array(
        self,
    ) -> np.ndarray | None:
        return self._array

    def clear(
        self,
    ) -> None:
        self._joint_count = 0
        self._array = None
        self._bytes = b""

    def sync_palette(
        self,
        *,
        mesh: Object3D,
        skin: Skin | None,
    ) -> None:
        if skin is None:
            self.clear()
            return

        self._ensure_capacity(
            skin,
        )

        assert self._array is not None

        mesh_inverse = np.linalg.inv(
            mesh.world_matrix.values,
        ).astype(
            np.float32,
            copy=False,
        )

        np.matmul(
            mesh_inverse,
            skin.skin_array,
            out=self._array,
        )

        self._bytes = np.ascontiguousarray(
            self._array.transpose(
                0,
                2,
                1,
            ).reshape(
                -1,
            ),
            dtype=np.float32,
        ).tobytes()

    def _ensure_capacity(
        self,
        skin: Skin,
    ) -> None:
        joint_count = skin.joint_count

        if self._joint_count == joint_count:
            return

        self._joint_count = joint_count

        self._array = np.empty(
            (
                joint_count,
                4,
                4,
            ),
            dtype=np.float32,
        )

        self._bytes = b""
