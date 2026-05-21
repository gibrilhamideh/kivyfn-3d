# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.config import Config

from kivyfn.three.render.shader import Shader
Config.set('input', 'mouse', 'mouse,disable_multitouch')


from kivy.app import App

from kivyfn.three.utils.color import random_color
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.math.vector import Vector3
from kivyfn.three.render.material import Material
from kivyfn.three.scene import Scene
from kivyfn.three.scene.object3d import Object3D
from kivyfn.three.primitive import Cube
from kivyfn.three.helpers import GridHelper, AxisHelper
from kivyfn.three.controls import InteractionController, BlenderCameraControls



class MainApp(App):
    def on_start(self):
        resources_path = Path(__file__).parent / "resources"

        model_path = resources_path / "models" / "glb" / "dashboard.glb"
        global_shader_path = resources_path / "shaders" / "basic" / "lambert.glsl"
        helper_shader_path = resources_path / "shaders" / "helper" / "unlit.glsl"

        loader = GlbLoader()
        objects = loader.load(model_path)

        self.scene = Scene(global_shader_path)

        # ---) attach interactions
        interactions = InteractionController()
        self.scene.attach(interactions)

        # ---) attach blender camera
        blender = BlenderCameraControls()
        self.scene.attach(blender, priority=100)


        # ---) Dashboard
        for name, mesh_data in objects.items():
            material = Material(name, color=random_color())
            node = Object3D(mesh_data, material, name=name)
            node.bind(on_release=self.on_test)
            self.scene.root.add_child(node)

        # ---) Cube
        # cube = Cube()
        # cube.bind(on_release=self.on_test)
        # self.scene.root.add_child(cube)

        # ---) Unlit Shader
        shader = Shader(helper_shader_path)

        # ---) Axis Heloper
        axis = AxisHelper()
        self.scene.root.add_child(axis)

        # ---) Grid Helper
        grid = GridHelper()
        self.scene.root.add_child(grid)

        self.root.add_widget(self.scene) # pyright: ignore

        self.scene.render()

    def on_test(self, instance, event):
        print("event: ", event)



if __name__ == "__main__":
    MainApp().run()
