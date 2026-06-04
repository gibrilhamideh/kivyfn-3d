# kivyfn/three/loaders/scene_loader.py

from __future__ import annotations

from kivyfn.three.loaders.glb.loader import GlbLoader
from kivyfn.three.loaders.glb.asset import GlbSceneAsset, GlbAsset

from kivyfn.three.loaders.obj.loader import ObjLoader
from kivyfn.three.loaders.obj.asset import ObjSceneAsset, ObjAsset


class SceneLoader:
    def __init__(self) -> None:
        self.glb = GlbLoader()
        self.obj = ObjLoader()

    def render_asset(
        self,
        scene,
        asset,
        context: str,
        **kwargs,
    ):
        if isinstance(asset, GlbAsset):
            return self.glb.render_asset(
                scene,
                asset,
                context,
                **kwargs,
            )

        if isinstance(asset, ObjAsset):
            return self.obj.render_asset(
                scene,
                asset,
                context,
                **kwargs,
            )

        raise TypeError(
            f"Unsupported asset type: {type(asset).__name__}"
        )

    def render_scene(
        self,
        scene,
        scene_asset,
        context: str,
        **kwargs,
    ):
        if isinstance(scene_asset, GlbSceneAsset):
            return self.glb.render_scene(
                scene,
                scene_asset,
                context,
                **kwargs,
            )

        if isinstance(scene_asset, ObjSceneAsset):
            return self.obj.render_scene(
                scene,
                scene_asset,
                context,
                **kwargs,
            )

        raise TypeError(
            f"Unsupported scene asset type: {type(scene_asset).__name__}"
        )
