# kivyfn/three/loaders/glb/loader.py
from __future__ import annotations
from typing import TYPE_CHECKING

from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.graph.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three import Scene
    from kivyfn.three.types import SceneObject
    from kivyfn.three.loaders.glb.blueprint import GlbBlueprint, GlbSceneBlueprint

class GlbLoader:
    def render_blueprint(
        self,
        scene: Scene,
        blueprint: GlbBlueprint,
        stage_name: str,
        *,
        parent: SceneObject | None = None,
    ) -> SceneObject:

        if blueprint.is_renderable:
            node = Object3D(
                name=blueprint.name,
                uid=blueprint.uid,
                geometry=blueprint.require_geometry(),
                material=blueprint.require_material(copy=True),
                transform=blueprint.transform.copy(),
            )

        else:
            node = Node3D(
                name=blueprint.name,
                uid=blueprint.uid,
                transform=blueprint.transform.copy(),
            )

        scene.render(
            node,
            parent=parent,
            stage_name=stage_name,
        )

        for child_blueprint in blueprint.children:
            self.render_blueprint(
                scene,
                child_blueprint,
                parent=node,
                stage_name=stage_name,
            )

        return node


    def render_scene_blueprint(
        self,
        scene: Scene,
        scene_blueprint: GlbSceneBlueprint,
        stage_name: str,
    ) -> list[SceneObject]:

        nodes: list[Node3D] = []

        for asset in scene_blueprint.tree:
            node = self.render_blueprint(
                scene,
                asset,
                stage_name=stage_name,
            )

            nodes.append(node)

        return nodes


