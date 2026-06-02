from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from kivyfn.three.objects.object3d import Object3D
    from kivyfn.three.scene.node import Node3D



SceneObject: TypeAlias = "Node3D | Object3D"


