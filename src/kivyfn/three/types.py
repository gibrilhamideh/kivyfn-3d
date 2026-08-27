# kivyfn/three/types.py

from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Literal
from collections.abc import Callable



if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.skinning.skinned_mesh import SkinnedMesh3D
    from kivyfn.three.skinning.skinned_model import SkinnedModel3D
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.parsers.glb.blueprint import GlbBlueprint, GlbInstance
    from kivyfn.three.parsers.obj.blueprint import ObjBlueprint, ObjAsset
    from kivyfn.three.graphics.gl.targets import ScreenTarget, Texture2DTarget, TextureCubeTarget

    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight

ViewportSource = Literal["scene", "local"]
FboSizeMode = Literal["fixed", "viewport"]


LightSource: TypeAlias = "DirectionalLight | PointLight | SpotLight"

SceneBlueprint: TypeAlias = "GlbBlueprint | ObjBlueprint"

StageTargets: TypeAlias = "ScreenTarget | Texture2DTarget | TextureCubeTarget"
RenderPassTarget: TypeAlias = "Texture2DTarget | TextureCubeTarget"

StageTargetKind = Literal[
    "screen",
    "texture-2d",
    "texture-cube",
]

SceneObject: TypeAlias = "Node3D | Object3D | SkinnedModel3D | SkinnedMesh3D | Light3D"
RenderableObject: TypeAlias = "Object3D | SkinnedMesh3D"


WalkFilter = Callable[["SceneObject"], bool]

Color = tuple[float, float, float, float]

CubeFaceName = Literal["px", "nx", "py", "ny", "pz", "nz"]

ShaderReloadEvent = Literal[
    "manual",
    "modified",
    "created",
    "moved",
]

MeshMode = Literal[
    "points",
    "line_strip",
    "line_loop",
    "lines",
    "triangles",
    "triangle_strip",
    "triangle_fan",
]

OverlayAnchor = Literal[
    "origin",
    "center",
    "top",
    "bottom",
    "left",
    "right",
    "front",
    "back",
]
