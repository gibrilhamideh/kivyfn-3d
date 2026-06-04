# kivyfn/three/loaders/scene_loader.py

from __future__ import annotations
from typing import TYPE_CHECKING

from kivyfn.three.loaders.glb.loader import GlbLoader
from kivyfn.three.loaders.glb.blueprint import GlbSceneBlueprint, GlbBlueprint

from kivyfn.three.loaders.obj.loader import ObjLoader
from kivyfn.three.loaders.obj.blueprint import ObjSceneBlueprint, ObjBlueprint

if TYPE_CHECKING:
    from kivyfn.three.types import SceneBlueprint, AssetBlueprint


class SceneLoader:
    def __init__(self) -> None:
        self.glb = GlbLoader()
        self.obj = ObjLoader()

    def render_blueprint(
        self,
        scene,
        blueprint: AssetBlueprint,
        stage_name: str,
        **kwargs,
    ):
        if isinstance(blueprint, GlbBlueprint):
            return self.glb.render_blueprint(
                scene,
                blueprint,
                stage_name,
                **kwargs,
            )

        if isinstance(blueprint, ObjBlueprint):
            return self.obj.render_blueprint(
                scene,
                blueprint,
                stage_name,
                **kwargs,
            )

        raise TypeError(
            f"Unsupported blueprint type: {type(blueprint).__name__}"
        )

    def render_scene_blueprint(
        self,
        scene,
        scene_blueprint: SceneBlueprint,
        stage_name: str,
        **kwargs,
    ):
        if isinstance(scene_blueprint, GlbSceneBlueprint):
            return self.glb.render_scene_blueprint(
                scene,
                scene_blueprint,
                stage_name,
                **kwargs,
            )

        if isinstance(scene_blueprint, GlbSceneBlueprint):
            return self.obj.render_scene_blueprint(
                scene,
                scene_blueprint,
                stage_name,
                **kwargs,
            )

        raise TypeError(
            f"Unsupported scene blueprint type: {type(scene_blueprint).__name__}"
        )
