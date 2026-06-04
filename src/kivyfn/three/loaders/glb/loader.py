# kivyfn/three/loaders/glb/loader.py
from __future__ import annotations
from typing import TYPE_CHECKING

from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.graph.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three import Scene
    from kivyfn.three.types import SceneObject
    from kivyfn.three.loaders.glb.asset import GlbAsset, GlbSceneAsset

class GlbLoader:
    def render_asset(
        self,
        scene: Scene,
        asset: GlbAsset,
        context: str,
        *,
        parent: SceneObject | None = None,
    ) -> SceneObject:

        if asset.is_renderable:
            node = Object3D(
                name=asset.name,
                uid=asset.uid,
                geometry=asset.require_geometry(),
                material=asset.require_material(copy=True),
                transform=asset.transform.copy(),
            )

        else:
            node = Node3D(
                name=asset.name,
                uid=asset.uid,
                transform=asset.transform.copy(),
            )

        scene.render(
            node,
            parent=parent,
            context=context,
        )

        for child_asset in asset.children:
            self.render_asset(
                scene,
                child_asset,
                parent=node,
                context=context,
            )

        return node


    def render_scene(
        self,
        scene: Scene,
        scene_asset: GlbSceneAsset,
        context: str,
    ) -> list[SceneObject]:

        nodes: list[Node3D] = []

        for asset in scene_asset.tree:
            node = self.render_asset(
                scene,
                asset,
                context=context,
            )

            nodes.append(node)

        return nodes


