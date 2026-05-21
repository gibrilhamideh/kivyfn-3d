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

        path = resources_path / "shaders" / "basic" / "lambert.glsl"
        shader = Shader(path)

        # ---) attach interactions
        interactions = InteractionController()
        self.scene.attach(interactions)

        # ---) attach blender camera
        blender = BlenderCameraControls()
        self.scene.attach(blender, priority=100)

        # ---) Dashboard
        for name, mesh_data in objects.items():
            material = Material(shader, name=name, color=random_color())
            node = Object3D(mesh_data, material, name=name, pickable=True)
            node.bind(on_release=self.on_test)
            self.scene.root.add_child(node)

        # ---) Unlit Shader
        helper_path = resources_path / "shaders" / "helper" / "unlit.glsl"
        helper_shader = Shader(helper_path)
        helper_material = Material(name="helper",shader=helper_shader)

        # ---) Axis Heloper
        axis = AxisHelper(material=helper_material)

        # ---) Grid Helper
        grid = GridHelper(
            size=100,
            divisions=100,
            material=Material(
                name="grid",
                color=[0.45, 0.45, 0.45, 1.0],
                shader=helper_shader,
            )
        )

        self.scene.root.add_child(axis)
        self.scene.root.add_child(grid)
        self.scene.render()

        self.root.add_widget(self.scene)  # pyright: ignore

    def on_test(self, instance, event):
        print("event: ", event)


if __name__ == "__main__":
    MainApp().run()
