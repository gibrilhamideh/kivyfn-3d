# kivyfn/three/loaders/obj/loader.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivyfn.three.assets.object3d import Object3D

if TYPE_CHECKING:
    from kivyfn.three import Scene
    from kivyfn.three.types import SceneObject
    from kivyfn.three.loaders.obj.asset import ObjAsset, ObjSceneAsset


class ObjLoader:
    def render_asset(
        self,
        scene: Scene,
        asset: ObjAsset,
        context: str,
        *,
        parent: SceneObject | None = None,
    ) -> Object3D:

        node = Object3D(
            name=asset.name,
            geometry=asset.geometry,
            material=asset.material.copy(),
            transform=asset.transform.copy(),
        )

        node.origin = asset.geometry.bounds.center

        scene.render(
            node,
            parent=parent,
            context=context,
        )

        return node

    def render_scene(
        self,
        scene: Scene,
        scene_asset: ObjSceneAsset,
        context: str,
    ) -> list[SceneObject]:

        nodes: list[SceneObject] = []

        for asset in scene_asset.walk_objects():
            node = self.render_asset(
                scene,
                asset,
                context=context,
            )

            nodes.append(node)

        return nodes
