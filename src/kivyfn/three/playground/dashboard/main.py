# kivyfn/three/playground/dashboard/main.py

from __future__ import annotations

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.controls import (
    BlenderCameraControls,
    InteractionController,
)
from kivyfn.three.helpers import (
    AxisHelper,
    GridHelper,
)
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.objects import Material
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.scene import Scene
from kivyfn.three.paths import THREE_MODEL_PATH, THREE_SHADER_PATH


class MainApp(App):

    def on_start(self):

        model_path = (
            THREE_MODEL_PATH
            / "dashboard.glb"
        )




        standard_shader = Shader(
            name="standard",
            path=(
                THREE_SHADER_PATH
                / "basic"
                / "standard.glsl"
            ),
        )

        helper_shader = Shader(
            name="helper",
            path=(
                THREE_SHADER_PATH
                / "helper"
                / "unlit.glsl"
            ),
        )

        self.scene = Scene()
        self.scene.create_context(
            name="main",
            shader=standard_shader,
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
            )
        )

        self.scene.add(
            axis,
            context="helper",
        )

        self.scene.add(
            grid,
            context="helper",
        )

        self.root.add_widget(self.scene)  # pyright: ignore

        loader = GlbLoader()
        scene = loader.load(model_path)
        self.scene.load_scene(
            scene,
            context="main",
        )


if __name__ == "__main__":
    MainApp().run()
