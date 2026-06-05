# kivyfn/three/loaders/obj/loader.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivyfn.three.assets.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three import Scene
    from kivyfn.three.types import SceneObject
    from kivyfn.three.loaders.obj.blueprint import ObjBlueprint, ObjSceneBlueprint


class ObjLoader:
    def render_blueprint(
        self,
        scene: Scene,
        blueprint: ObjBlueprint,
        stage_name: str,
        *,
        parent: SceneObject | None = None,
    ) -> Object3D:

        node = Object3D(
            name=blueprint.name,
            geometry=blueprint.geometry,
            material=blueprint.material.copy(),
            transform=blueprint.transform.copy(),
        )

        node.origin = blueprint.geometry.bounds.center

        scene.render(
            node,
            parent=parent,
            stage=stage_name,
        )

        return node

    def render_scene_blueprint(
        self,
        scene: Scene,
        scene_asset: ObjSceneBlueprint,
        stage_name: str,
    ) -> list[SceneObject]:

        nodes: list[SceneObject] = []

        for asset in scene_asset.walk_objects():
            node = self.render_blueprint(
                scene,
                asset,
                stage_name=stage_name,
            )

            nodes.append(node)

        return nodes
