# kivyfn/three/playground/relationship/main.py

from __future__ import annotations

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.controls import BlenderCameraControls, InteractionController
from kivyfn.three.helpers import AxisHelper, GridHelper
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.objects import Material
from kivyfn.three.paths import RESOURCES_PATH
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.scene import Scene


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
        scene = loader.load(
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
                base_color=[0.45, 0.45, 0.45, 1.0]
            ),
        )

        self.scene.add(axis, context="helper")
        self.scene.add(grid, context="helper")
        self.scene.load_scene(scene, context="main")

        self.root.add_widget(self.scene)  # pyright: ignore



if __name__ == "__main__":
    MainApp().run()
