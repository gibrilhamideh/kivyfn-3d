
# kivyfn/three/skinning/skin.py

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3
from kivyfn.three.skinning.skeleton import Skeleton


@dataclass(slots=True)
class Skin:
    name: str
    skeleton: Skeleton

    joint_names: tuple[str, ...]
    joint_indices: tuple[int, ...]
    joint_bone_indices: np.ndarray
    inverse_bind_matrices: tuple[Matrix4, ...]

    inverse_bind_array: np.ndarray = field(
        init=False,
        repr=False,
    )
    skin_array: np.ndarray = field(
        init=False,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        joint_count = len(
            self.joint_names,
        )

        if len(self.joint_indices) != joint_count:
            raise ValueError(
                "Skin joint_indices must have the same length as joint_names. "
                f"Got {len(self.joint_indices)} joint indices and "
                f"{joint_count} joint names."
            )

        if len(self.joint_bone_indices) != joint_count:
            raise ValueError(
                "Skin joint_bone_indices must have the same length as joint_names. "
                f"Got {len(self.joint_bone_indices)} joint bone indices and "
                f"{joint_count} joint names."
            )

        if len(self.inverse_bind_matrices) != joint_count:
            raise ValueError(
                "Skin inverse_bind_matrices must have the same length as joint_names. "
                f"Got {len(self.inverse_bind_matrices)} inverse bind matrices and "
                f"{joint_count} joint names."
            )

        self.joint_bone_indices = np.asarray(
            self.joint_bone_indices,
            dtype=np.int32,
        )

        bone_count = self.skeleton.bone_count

        for joint_index, bone_index in enumerate(
            self.joint_bone_indices,
        ):
            if bone_index < 0 or bone_index >= bone_count:
                raise ValueError(
                    f"Skin {self.name!r} joint {joint_index} references invalid "
                    f"bone index {int(bone_index)}. Skeleton {self.skeleton.name!r} "
                    f"has {bone_count} bones."
                )

        self.inverse_bind_array = np.stack(
            [
                matrix.values
                for matrix in self.inverse_bind_matrices
            ],
            axis=0,
        ).astype(
            np.float32,
            copy=False,
        )

        self.skin_array = np.repeat(
            np.eye(
                4,
                dtype=np.float32,
            )[None, :, :],
            joint_count,
            axis=0,
        )

    @property
    def joint_count(
        self,
    ) -> int:
        return len(
            self.joint_names,
        )

    @property
    def bone_count(
        self,
    ) -> int:
        return self.skeleton.bone_count

    def index_of_bone(
        self,
        gltf_index: int,
    ) -> int | None:
        return self.skeleton.index_of_bone(
            gltf_index,
        )

    def require_bone(
        self,
        gltf_index: int,
    ) -> int:
        return self.skeleton.require_bone(
            gltf_index,
        )

    def set_bone_translation(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skeleton.set_bone_translation(
            index,
            value,
        )

    def set_bone_rotation(
        self,
        index: int,
        value: Quaternion,
    ) -> None:
        self.skeleton.set_bone_rotation(
            index,
            value,
        )

    def set_bone_scale(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skeleton.set_bone_scale(
            index,
            value,
        )

    def set_joint_translation(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.set_bone_translation(
            int(
                self.joint_bone_indices[index],
            ),
            value,
        )

    def set_joint_rotation(
        self,
        index: int,
        value: Quaternion,
    ) -> None:
        self.set_bone_rotation(
            int(
                self.joint_bone_indices[index],
            ),
            value,
        )

    def set_joint_scale(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.set_bone_scale(
            int(
                self.joint_bone_indices[index],
            ),
            value,
        )


    def sync_skin(
        self,
    ) -> None:
        np.matmul(
            self.skeleton.bone_world_array[self.joint_bone_indices],
            self.inverse_bind_array,
            out=self.skin_array,
        )
