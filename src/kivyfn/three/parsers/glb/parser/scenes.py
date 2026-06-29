# kivyfn/three/parsers/glb/parser/scenes.py

from __future__ import annotations

from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.nodes import GlbNodes
from kivyfn.three.parsers.glb.scene import GlbScene


class GlbScenes:
    def __init__(
        self,
        context: GlbContext,
        nodes: GlbNodes,
    ) -> None:
        self.context = context
        self.nodes = nodes

    def load(
        self,
    ) -> None:
        gltf = self.context.gltf
        raw_scenes = list(gltf.scenes or [])

        if not raw_scenes:
            raise ValueError(
                "GLB contains no scenes. "
                "kivyfn.three requires at least one glTF scene."
            )

        for index, raw_scene in enumerate(raw_scenes):
            name = (
                raw_scene.name
                or f"Scene.{index:03d}"
            )

            scene = GlbScene(
                name=name,
            )

            for node_index in list(raw_scene.nodes or []):
                scene.roots.append(
                    self.nodes.cached(node_index),
                )

            if scene.is_empty:
                raise ValueError(
                    f"GLB scene {index} has no root nodes."
                )

            self.context.blueprint.scenes.append(scene)

    def finalize(
        self,
    ) -> None:
        blueprint = self.context.blueprint

        if not blueprint.scenes:
            raise ValueError(
                "GLB contains no scenes."
            )

        index = self.context.gltf.scene

        if index is None:
            blueprint.set_default_scene(
                blueprint.scenes[0],
            )
            return

        if (
            index < 0
            or index >= len(blueprint.scenes)
        ):
            raise ValueError(
                f"Invalid default GLB scene index: {index!r}"
            )

        blueprint.set_default_scene(
            blueprint.scenes[index],
        )
