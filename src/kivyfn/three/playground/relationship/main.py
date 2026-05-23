# kivyfn/three/playground/relationship/main.py

from __future__ import annotations

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.controls import BlenderCameraControls, InteractionController
from kivyfn.three.helpers import AxisHelper, GridHelper
from kivyfn.three.loaders.asset import AssetObject
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.math.vector import Vector3
from kivyfn.three.objects import Material
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.paths import RESOURCES_PATH
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene import Scene
from kivyfn.three.scene.node import Node3D
from kivyfn.three.utils.color import random_color


class MainApp(App):
    def on_start(self):
        self.scene = Scene()

        lambert_shader = Shader(
            name="lambert",
            path=RESOURCES_PATH / "shaders" / "basic" / "lambert.glsl",
        )

        helper_shader = Shader(
            name="helper",
            path=RESOURCES_PATH / "shaders" / "helper" / "unlit.glsl",
        )

        loader = GlbLoader()
        assets = loader.load(
            RESOURCES_PATH / "models" / "glb" / "Cube.glb"
        )

        self.scene.create_context(
            name="main",
            shader=lambert_shader,
        )

        self.scene.create_context(
            name="helper",
            shader=helper_shader,
        )

        self.scene.attach_controller(
            InteractionController(),
        )

        self.scene.attach_controller(
            BlenderCameraControls(),
            priority=100,
        )

        axis = AxisHelper()

        grid = GridHelper(
            size=100,
            divisions=100,
            material=Material(
                name="grid",
                uniforms={
                    "object_color": [0.45, 0.45, 0.45, 1.0],
                },
            ),
        )

        for root_asset in assets.tree:
            self._add_asset_tree(root_asset)

        self.scene.add(axis, context="helper")
        self.scene.add(grid, context="helper")

        self.root.add_widget(self.scene)  # pyright: ignore

    def _add_asset_tree(
        self,
        asset: AssetObject,
        parent: Node3D | None = None,
    ) -> Node3D:
        if asset.is_renderable:
            material = Material(
                name=asset.name,
                uniforms={
                    "object_color": random_color(),
                },
            )

            node = Object3D(
                name=asset.name,
                geometry=asset.require_geometry(),
                material=material,
                transform=asset.transform,
                pickable=True
            )

            node.bind(
                on_release=self._on_object_release,
            )
        else:
            node = Node3D(
                name=asset.name,
                transform=asset.transform,
            )

        self.scene.add(
            node,
            parent=parent,
            context="main",
        )

        for child_asset in asset.children:
            self._add_asset_tree(
                child_asset,
                parent=node,
            )

        return node

    def _on_object_release(
        self,
        node: Object3D,
        event,
    ) -> None:

        node.rotate_by(
            angle_degrees=15.0,
            axis=Vector3(0.0, 1.0, 0.0),
        )



if __name__ == "__main__":
    MainApp().run()
