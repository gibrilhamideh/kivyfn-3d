# kivyfn/three/assets/deformation.py

from __future__ import annotations

from dataclasses import dataclass, field
from array import array
import numpy as np

from kivyfn.three.assets.skin import Skin
from kivyfn.three.graph.node import Node3D


EMPTY_MATRIX4_ARRAY = array("f")


@dataclass(slots=True)
class Deformation:
    morph_weights: list[float] = field(default_factory=list)
    skin: Skin | None = None

    _joint_world_array: np.ndarray | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _joint_bind_array: np.ndarray | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _joint_palette_array: np.ndarray | None = field(
        default=None,
        init=False,
        repr=False,
    )

    _joint_uniform_data: array = field(
        default_factory=lambda: EMPTY_MATRIX4_ARRAY,
        init=False,
        repr=False,
    )

    _joint_count: int = field(
        default=0,
        init=False,
        repr=False,
    )

    @property
    def has_morph_weights(self) -> bool:
        return bool(self.morph_weights)

    @property
    def has_skin(self) -> bool:
        return self.skin is not None

    @property
    def joint_count(self) -> int:
        return self._joint_count

    @property
    def joint_uniform_data(self) -> array:
        return self._joint_uniform_data

    def clear_joint_matrices(self) -> None:
        self._joint_count = 0
        self._joint_uniform_data = EMPTY_MATRIX4_ARRAY

    def sync_joint_matrices_for(
        self,
        mesh: Node3D,
    ) -> None:
        skin = self.skin

        if skin is None:
            self.clear_joint_matrices()
            return

        self._ensure_skin_buffers(skin)

        assert self._joint_world_array is not None
        assert self._joint_bind_array is not None
        assert self._joint_palette_array is not None

        skin.fill_joint_world_array(
            self._joint_world_array,
        )

        np.matmul(
            self._joint_world_array,
            skin.inverse_bind_array,
            out=self._joint_bind_array,
        )

        mesh_inverse = np.linalg.inv(
            mesh.world_matrix.values,
        ).astype(np.float32)

        np.matmul(
            mesh_inverse,
            self._joint_bind_array,
            out=self._joint_palette_array,
        )

        self._joint_uniform_data = array(
            "f",
            self._joint_palette_array.transpose(0, 2, 1).ravel(),
        )

    def _ensure_skin_buffers(
        self,
        skin: Skin,
    ) -> None:
        joint_count = skin.joint_count

        if self._joint_count == joint_count:
            return

        self._joint_count = joint_count

        self._joint_world_array = np.empty(
            (joint_count, 4, 4),
            dtype=np.float32,
        )

        self._joint_bind_array = np.empty(
            (joint_count, 4, 4),
            dtype=np.float32,
        )

        self._joint_palette_array = np.empty(
            (joint_count, 4, 4),
            dtype=np.float32,
        )

        self._joint_uniform_data = array(
            "f",
            [0.0] * joint_count * 16,
        )
