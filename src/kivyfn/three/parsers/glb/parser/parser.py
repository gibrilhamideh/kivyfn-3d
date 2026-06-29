# kivyfn/three/parsers/glb/parser/parser.py

from __future__ import annotations

from pathlib import Path

from kivyfn.three.parsers.glb.blueprint import GlbBlueprint
from kivyfn.three.parsers.glb.parser.accessors import GlbAccessor
from kivyfn.three.parsers.glb.parser.animations import GlbAnimations
from kivyfn.three.parsers.glb.parser.context import GlbOptions
from kivyfn.three.parsers.glb.parser.geometry import GlbGeometry
from kivyfn.three.parsers.glb.parser.loader import GlbLoader
from kivyfn.three.parsers.glb.parser.materials import GlbMaterials
from kivyfn.three.parsers.glb.parser.nodes import GlbNodes
from kivyfn.three.parsers.glb.parser.registry import GlbRegistry
from kivyfn.three.parsers.glb.parser.scenes import GlbScenes
from kivyfn.three.parsers.glb.parser.skins import GlbSkins
from kivyfn.three.parsers.glb.parser.textures import GlbTextures


class GlbParser:
    def __init__(
        self,
        flip_v: bool = False,
        flip_winding: bool = False,
    ) -> None:
        self.options = GlbOptions(
            flip_v=flip_v,
            flip_winding=flip_winding,
        )

    def parse(
        self,
        filename: str | Path,
    ) -> GlbBlueprint:
        context = GlbLoader().load(
            filename=filename,
            options=self.options,
        )

        accessor = GlbAccessor(
            context,
        )

        registry = GlbRegistry(
            context,
        )

        textures = GlbTextures(
            context=context,
            accessor=accessor,
        )

        materials = GlbMaterials(
            context=context,
            textures=textures,
        )

        geometry = GlbGeometry(
            context=context,
            accessor=accessor,
        )

        nodes = GlbNodes(
            context=context,
            accessor=accessor,
            registry=registry,
            geometry=geometry,
            materials=materials,
        )

        scenes = GlbScenes(
            context=context,
            nodes=nodes,
        )

        skins = GlbSkins(
            context=context,
            accessor=accessor,
        )

        animations = GlbAnimations(
            context=context,
            accessor=accessor,
        )

        scenes.load()
        scenes.finalize()

        context.blueprint.skins = skins.load()
        skins.validate()

        context.blueprint.animations = animations.load()

        return context.blueprint


__all__ = (
    "GlbParser",
)
