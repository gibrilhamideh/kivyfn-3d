# kivyfn/three/skinning/skeleton.py

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform
from kivyfn.three.math.vector import Vector3


@dataclass(slots=True)
class Skeleton:
    name: str

    bone_names: tuple[str, ...]
    bone_indices: tuple[int, ...]
    parent_bone_indices: np.ndarray
    bone_local_transforms: tuple[Transform, ...]

    bone_index_by_gltf_index: dict[int, int] = field(
        init=False,
        repr=False,
    )
    bone_local_array: np.ndarray = field(
        init=False,
        repr=False,
    )
    bone_world_array: np.ndarray = field(
        init=False,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        bone_count = len(
            self.bone_names,
        )

        if len(self.bone_indices) != bone_count:
            raise ValueError(
                "Skeleton bone_indices must have the same length as bone_names. "
                f"Got {len(self.bone_indices)} bone indices and "
                f"{bone_count} bone names."
            )

        if len(self.parent_bone_indices) != bone_count:
            raise ValueError(
                "Skeleton parent_bone_indices must have the same length as "
                "bone_names. "
                f"Got {len(self.parent_bone_indices)} parent bone indices and "
                f"{bone_count} bone names."
            )

        if len(self.bone_local_transforms) != bone_count:
            raise ValueError(
                "Skeleton bone_local_transforms must have the same length as "
                "bone_names. "
                f"Got {len(self.bone_local_transforms)} bone transforms and "
                f"{bone_count} bone names."
            )

        self.bone_index_by_gltf_index = {
            gltf_index: index
            for index, gltf_index in enumerate(
                self.bone_indices,
            )
        }

        if len(self.bone_index_by_gltf_index) != bone_count:
            raise ValueError(
                "Skeleton bone_indices contains duplicate glTF node indices."
            )

        self.parent_bone_indices = np.asarray(
            self.parent_bone_indices,
            dtype=np.int32,
        )

        for bone_index, parent_bone_index in enumerate(
            self.parent_bone_indices,
        ):
            parent_bone_index = int(
                parent_bone_index,
            )

            if parent_bone_index < -1 or parent_bone_index >= bone_count:
                raise ValueError(
                    f"Skeleton {self.name!r} bone {bone_index} has invalid "
                    f"parent bone index {parent_bone_index}. Skeleton has "
                    f"{bone_count} bones."
                )

            if parent_bone_index >= bone_index:
                raise ValueError(
                    f"Skeleton {self.name!r} bone {bone_index} has parent "
                    f"{parent_bone_index}, but parent bones must appear before "
                    "child bones in the flat skeleton order."
                )

        self.bone_local_array = np.stack(
            [
                transform.matrix.values
                for transform in self.bone_local_transforms
            ],
            axis=0,
        ).astype(
            np.float32,
            copy=False,
        )

        self.bone_world_array = np.repeat(
            np.eye(
                4,
                dtype=np.float32,
            )[None, :, :],
            bone_count,
            axis=0,
        )

    @property
    def bone_count(
        self,
    ) -> int:
        return len(
            self.bone_names,
        )

    def index_of_bone(
        self,
        gltf_index: int,
    ) -> int | None:
        return self.bone_index_by_gltf_index.get(
            gltf_index,
        )

    def require_bone(
        self,
        gltf_index: int,
    ) -> int:
        index = self.index_of_bone(
            gltf_index,
        )

        if index is None:
            raise KeyError(
                f"Skeleton {self.name!r} has no bone for glTF node index "
                f"{gltf_index}."
            )

        return index

    def set_bone_translation(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        transform = self.bone_local_transforms[index]

        transform.set_translation(
            value,
        )

        self.bone_local_array[index] = transform.matrix.values

    def set_bone_rotation(
        self,
        index: int,
        value: Quaternion,
    ) -> None:
        transform = self.bone_local_transforms[index]

        transform.set_rotation(
            value,
        )

        self.bone_local_array[index] = transform.matrix.values

    def set_bone_scale(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        transform = self.bone_local_transforms[index]

        transform.set_scale(
            value,
        )

        self.bone_local_array[index] = transform.matrix.values

    def sync_bones(
        self,
        root_world_matrix: Matrix4,
    ) -> None:
        parent_bone_indices = self.parent_bone_indices
        bone_local_array = self.bone_local_array
        bone_world_array = self.bone_world_array
        root_world = root_world_matrix.values

        for bone_index in range(
            self.bone_count,
        ):
            parent_bone_index = int(
                parent_bone_indices[bone_index],
            )

            if parent_bone_index < 0:
                bone_world_array[bone_index] = (
                    root_world
                    @ bone_local_array[bone_index]
                )
            else:
                bone_world_array[bone_index] = (
                    bone_world_array[parent_bone_index]
                    @ bone_local_array[bone_index]
                )
