# kivyfn/three/types.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Literal
from collections.abc import Callable



if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.loaders.glb.blueprint import GlbBlueprint, GlbSceneBlueprint
    from kivyfn.three.loaders.obj.blueprint import ObjBlueprint, ObjSceneBlueprint
    from kivyfn.three.render.context import RenderContext, RenderPass

    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight


LightSource: TypeAlias = "DirectionalLight | PointLight | SpotLight"

SceneBlueprint: TypeAlias = "GlbSceneBlueprint | ObjSceneBlueprint"
AssetBlueprint: TypeAlias = "GlbBlueprint | ObjBlueprint"

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

RenderPassName: TypeAlias = str
RenderContextName: TypeAlias = str
RenderStageName: TypeAlias = str
ViewName: TypeAlias = str
LightName: TypeAlias = str


WalkFilter = Callable[["SceneObject"], bool]
