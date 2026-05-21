# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.controls import BlenderCameraControls, InteractionController
from kivyfn.three.helpers import AxisHelper, GridHelper
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.render.material import Material
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene import Scene
from kivyfn.three.scene.object3d import Object3D
from kivyfn.three.utils.color import random_color


class MainApp(App):
    def on_start(self):
        resources_path = Path(__file__).parent / "resources"
        model_path = resources_path / "models" / "glb" / "dashboard.glb"

        loader = GlbLoader()
        objects = loader.load(model_path)

        self.scene = Scene()

        # --- Shaders
        lambert_shader = Shader(
            name="lambert",
            path=resources_path / "shaders" / "basic" / "lambert.glsl",
        )

        helper_shader = Shader(
            name="helper",
            path=resources_path / "shaders" / "helper" / "unlit.glsl",
        )

        # --- Contexts
        main_context = self.scene.create_context(
            name="main",
            shader=lambert_shader,
        )

        helper_context = self.scene.create_context(
            name="helper",
            shader=helper_shader,
        )

        # --- Controllers
        self.scene.attach_controller(InteractionController())
        self.scene.attach_controller(BlenderCameraControls(), priority=100)

        # --- Dashboard objects
        for name, mesh_data in objects.items():
            material = Material(
                name=name,
                uniforms={
                    "object_color": random_color(),
                },
            )

            node = Object3D(
                mesh_data=mesh_data,
                material=material,
                name=name,
                pickable=True,
            )

            node.bind(on_release=self.on_test)

            self.scene.add(
                node,
                context=main_context,
            )

        # --- Helpers
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

        self.scene.add(axis, context=helper_context)
        self.scene.add(grid, context=helper_context)

        self.scene.build()

        self.root.add_widget(self.scene)  # pyright: ignore

    def on_test(self, instance, event):
        print("event: ", event)


if __name__ == "__main__":
    MainApp().run()
