# kivyfn/three/assets/skin.py

from __future__ import annotations

from dataclasses import dataclass

from kivyfn.three.graph.node import Node3D
from kivyfn.three.math.matrix import Matrix4


@dataclass(slots=True)
class Skin:
    joints: tuple[Node3D, ...]
    inverse_bind_matrices: tuple[Matrix4, ...]
    name: str = ""

    def __post_init__(self) -> None:
        if len(self.joints) != len(self.inverse_bind_matrices):
            raise ValueError(
                "Skin joints and inverse_bind_matrices must have the same length. "
                f"Got {len(self.joints)} joints and "
                f"{len(self.inverse_bind_matrices)} inverse bind matrices."
            )

    @property
    def joint_count(self) -> int:
        return len(self.joints)

    def joint_matrices_for(
        self,
        mesh: Node3D,
    ) -> list[Matrix4]:
        mesh_inverse = mesh.world_matrix.inverse()

        return [
            mesh_inverse @ joint.world_matrix @ inverse_bind_matrix
            for joint, inverse_bind_matrix in zip(
                self.joints,
                self.inverse_bind_matrices,
            )
        ]

    def joint_matrix_for(
        self,
        mesh: Node3D,
        index: int,
    ) -> Matrix4:
        if index < 0 or index >= len(self.joints):
            raise IndexError(
                f"Skin joint index out of range: {index}. "
                f"Joint count is {len(self.joints)}."
            )

        mesh_inverse = mesh.world_matrix.inverse()
        joint = self.joints[index]
        inverse_bind_matrix = self.inverse_bind_matrices[index]

        return mesh_inverse @ joint.world_matrix @ inverse_bind_matrix
