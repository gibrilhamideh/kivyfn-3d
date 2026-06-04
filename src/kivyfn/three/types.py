# kivyfn/three/types.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Literal



if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.loaders.glb.blueprint import GlbBlueprint, GlbSceneBlueprint
    from kivyfn.three.loaders.obj.blueprint import ObjBlueprint, ObjSceneBlueprint
    from kivyfn.three.render.context import RenderContext, RenderPass



SceneBlueprint: TypeAlias = "GlbSceneBlueprint | ObjSceneBlueprint"
AssetBlueprint: TypeAlias = " GlbBlueprint | ObjBlueprint"

RenderStage: TypeAlias = "RenderPass | RenderContext"

SceneObject: TypeAlias = "Node3D | Object3D"

RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "id",
]
