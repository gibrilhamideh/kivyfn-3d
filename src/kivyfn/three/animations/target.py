# kivyfn/three/animations/target.py

from __future__ import annotations

from kivyfn.three.graph.node import Node3D
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3
from kivyfn.three.skinning.skinned_model import SkinnedModel3D


class NodeAnimationTarget:
    __slots__ = ("node",)

    def __init__(
        self,
        node: Node3D,
    ) -> None:
        self.node = node

    def set_translation(
        self,
        value: Vector3,
    ) -> None:
        self.node.set_translation(
            value,
        )

    def set_rotation(
        self,
        value: Quaternion,
    ) -> None:
        self.node.set_rotation(
            value,
        )

    def set_scale(
        self,
        value: Vector3,
    ) -> None:
        self.node.set_scale(
            value,
        )

    def set_weights(
        self,
        value: tuple[float, ...],
    ) -> None:
        self.node.set_morph_weights(
            value,
        )


class BoneAnimationTarget:
    __slots__ = (
        "model",
        "bone_index",
    )

    def __init__(
        self,
        *,
        model: SkinnedModel3D,
        bone_index: int,
    ) -> None:
        self.model = model
        self.bone_index = bone_index

    def set_translation(
        self,
        value: Vector3,
    ) -> None:
        self.model.set_bone_translation(
            self.bone_index,
            value,
        )

    def set_rotation(
        self,
        value: Quaternion,
    ) -> None:
        self.model.set_bone_rotation(
            self.bone_index,
            value,
        )

    def set_scale(
        self,
        value: Vector3,
    ) -> None:
        self.model.set_bone_scale(
            self.bone_index,
            value,
        )

    def set_weights(
        self,
        value: tuple[float, ...],
    ) -> None:
        return


class MultiBoneAnimationTarget:
    __slots__ = ("targets",)

    def __init__(
        self,
        targets: tuple[BoneAnimationTarget, ...],
    ) -> None:
        self.targets = targets

    def set_translation(
        self,
        value: Vector3,
    ) -> None:
        for target in self.targets:
            target.set_translation(
                value,
            )

    def set_rotation(
        self,
        value: Quaternion,
    ) -> None:
        for target in self.targets:
            target.set_rotation(
                value,
            )

    def set_scale(
        self,
        value: Vector3,
    ) -> None:
        for target in self.targets:
            target.set_scale(
                value,
            )

    def set_weights(
        self,
        value: tuple[float, ...],
    ) -> None:
        for target in self.targets:
            target.set_weights(
                value,
            )
