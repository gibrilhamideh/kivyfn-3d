from __future__ import annotations

from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3
from kivyfn.three.graph.node import Node3D


class AnimationApplication:

    @staticmethod
    def translation(
        node: Node3D,
        value: Vector3,
    ) -> None:
        node.set_translation(value)

    @staticmethod
    def rotation(
        node: Node3D,
        value: Quaternion,
    ) -> None:
        node.set_rotation(value)

    @staticmethod
    def scale(
        node: Node3D,
        value: Vector3,
    ) -> None:
        node.set_scale(value)

    @staticmethod
    def weights(
        node: Node3D,
        value: tuple[float, ...],
    ) -> None:
        node.set_morph_weights(value)


