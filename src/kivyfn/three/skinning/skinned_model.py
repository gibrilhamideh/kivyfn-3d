# kivyfn/three/skinning/skinned_model.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from kivyfn.three.graph.node import Node3D
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.skinning.skin import Skin
    from kivyfn.three.skinning.skinned_mesh import SkinnedMesh3D


class SkinnedModel3D(Node3D):
    def __init__(
        self,
        *,
        skin: Skin,
        **kwargs,
    ) -> None:
        super().__init__(
            **kwargs,
        )

        self.skin = skin
        self._skinned_meshes: list[SkinnedMesh3D] = []

        self._bones_dirty = True
        self._skin_dirty = True

    @property
    def kind(
        self,
    ):
        return "skinned_model"

    @property
    def bones_dirty(
        self,
    ) -> bool:
        return self._bones_dirty

    @property
    def skin_dirty(
        self,
    ) -> bool:
        return self._skin_dirty

    @property
    def skinned_meshes(
        self,
    ) -> tuple[SkinnedMesh3D, ...]:
        return tuple(
            self._skinned_meshes,
        )

    def attach_skinned_mesh(
        self,
        mesh: SkinnedMesh3D,
    ) -> None:
        if mesh in self._skinned_meshes:
            raise ValueError(
                f"SkinnedModel3D {self.name!r} already has skinned mesh "
                f"{mesh.name!r}."
            )

        if mesh._skinned_model is not None:
            raise ValueError(
                f"SkinnedMesh3D {mesh.name!r} is already attached to "
                f"SkinnedModel3D {mesh._skinned_model.name!r}."
            )

        mesh._skinned_model = self

        self._skinned_meshes.append(
            mesh,
        )

    def detach_skinned_mesh(
        self,
        mesh: SkinnedMesh3D,
    ) -> None:
        try:
            self._skinned_meshes.remove(
                mesh,
            )
        except ValueError as exc:
            raise ValueError(
                f"SkinnedModel3D {self.name!r} does not have skinned mesh "
                f"{mesh.name!r}."
            ) from exc

        mesh._skinned_model = None
        mesh.clear_skin_palette()

    def has_skinned_mesh(
        self,
        mesh: SkinnedMesh3D,
    ) -> bool:
        return mesh in self._skinned_meshes

    def iter_skinned_meshes(
        self,
    ) -> Iterator[SkinnedMesh3D]:
        return iter(
            self._skinned_meshes,
        )

    def mark_bones_dirty(
        self,
        *,
        queue: bool = True,
    ) -> None:
        self._bones_dirty = True
        self._skin_dirty = True

        if queue and self.scene is not None:
            self.scene.renderer.queue_skinned_model(
                self,
            )

    def mark_skin_dirty(
        self,
        *,
        queue: bool = True,
    ) -> None:
        self._skin_dirty = True

        if queue and self.scene is not None:
            self.scene.renderer.queue_skinned_model(
                self,
            )

    def clear_skin_dirty(
        self,
    ) -> None:
        self._bones_dirty = False
        self._skin_dirty = False

    def set_bone_translation(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skin.set_bone_translation(
            index,
            value,
        )

        self.mark_bones_dirty()

    def set_bone_rotation(
        self,
        index: int,
        value: Quaternion,
    ) -> None:
        self.skin.set_bone_rotation(
            index,
            value,
        )

        self.mark_bones_dirty()

    def set_bone_scale(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skin.set_bone_scale(
            index,
            value,
        )

        self.mark_bones_dirty()

    def set_joint_translation(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skin.set_joint_translation(
            index,
            value,
        )

        self.mark_bones_dirty()

    def set_joint_rotation(
        self,
        index: int,
        value: Quaternion,
    ) -> None:
        self.skin.set_joint_rotation(
            index,
            value,
        )

        self.mark_bones_dirty()

    def set_joint_scale(
        self,
        index: int,
        value: Vector3,
    ) -> None:
        self.skin.set_joint_scale(
            index,
            value,
        )

        self.mark_bones_dirty()

    def sync_skin(
        self,
    ) -> None:
        if not self._skin_dirty:
            return

        if self._bones_dirty:
            self.skin.skeleton.sync_bones(
                self.world_matrix,
            )

        self.skin.sync_skin()
        self.clear_skin_dirty()
