# kivyfn/three/assets/skin.py

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from kivyfn.three.graph.node import Node3D
from kivyfn.three.math.matrix import Matrix4


@dataclass(slots=True)
class Skin:
    joints: tuple[Node3D, ...]
    inverse_bind_matrices: tuple[Matrix4, ...]
    name: str = ""

    inverse_bind_array: np.ndarray = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if len(self.joints) != len(self.inverse_bind_matrices):
            raise ValueError(
                "Skin joints and inverse_bind_matrices must have the same length. "
                f"Got {len(self.joints)} joints and "
                f"{len(self.inverse_bind_matrices)} inverse bind matrices."
            )

        self.inverse_bind_array = np.stack(
            [
                matrix.values
                for matrix in self.inverse_bind_matrices
            ],
            axis=0,
        ).astype(np.float32)

    @property
    def joint_count(self) -> int:
        return len(self.joints)

    def fill_joint_world_array(
        self,
        out: np.ndarray,
    ) -> None:
        for index, joint in enumerate(self.joints):
            out[index] = joint.world_matrix.values
