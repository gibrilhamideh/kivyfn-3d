from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, Literal

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext, RenderPass

RenderStage: TypeAlias = "RenderPass | RenderContext"


RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "id",
]

