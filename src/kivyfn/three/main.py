# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock

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
        self.pending_objects = list(objects.items())

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
        self.scene.create_context(
            name="main",
            shader=lambert_shader,
        )

        self.scene.create_context(
            name="helper",
            shader=helper_shader,
        )

        # --- Controllers
        self.scene.attach_controller(InteractionController())
        self.scene.attach_controller(BlenderCameraControls(), priority=100)

        # --- Helpers load immediately
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

        self.scene.add(axis, context="helper")
        self.scene.add(grid, context="helper")

        self.root.add_widget(self.scene)  # pyright: ignore

        # --- Lazy load dashboard objects
        self.lazy_load_event = Clock.schedule_interval(
            self.lazy_load_next_object,
            0.2,
        )

    def lazy_load_next_object(self, dt):
        if not self.pending_objects:
            self.lazy_load_event.cancel()
            return False

        name, geometry = self.pending_objects.pop(0)

        material = Material(
            name=name,
            uniforms={
                "object_color": random_color(),
            },
        )

        object3d = Object3D(
            geometry=geometry,
            material=material,
            name=name,
            pickable=True,
        )

        object3d.bind(on_release=self.on_release)

        self.scene.add(
            object3d,
            context="main",
        )


        return True

    def on_release(self, instance, event):
        print("event: ", event)
        self.change_color(event.node)

    def change_color(self, object3d):
        object3d.material.set_uniform(
            "object_color",
            random_color(),
        )


if __name__ == "__main__":
    MainApp().run()
