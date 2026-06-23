# kivyfn/three/types.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Literal
from collections.abc import Callable



if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.parsers.glb.blueprint import GlbBlueprint, GlbAsset
    from kivyfn.three.parsers.obj.blueprint import ObjBlueprint, ObjAsset
    from kivyfn.three.render.context import RenderContext, RenderPass

    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight

ViewportMode = Literal["scene", "local"]
FboSizeMode = Literal["fixed", "viewport"]


LightSource: TypeAlias = "DirectionalLight | PointLight | SpotLight"

SceneBlueprint: TypeAlias = "GlbBlueprint | ObjBlueprint"
AssetBlueprint: TypeAlias = "GlbAsset | ObjAsset"

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
LightName: TypeAlias = str


WalkFilter = Callable[["SceneObject"], bool]
