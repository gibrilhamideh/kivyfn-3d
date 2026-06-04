from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias

from kivyfn.three.render.types import RenderStage
from kivyfn.three.render.types import RenderPassOutput

if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D


SceneObject: TypeAlias = "Node3D | Object3D"
