
# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.clock import Clock, ClockEvent

from kivyfn.three.controls import (
    BlenderCameraControls,
    InteractionController,
)
from kivyfn.three.helpers import (
    AxisHelper,
    GridHelper,
)
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.math.vector import Vector3
from kivyfn.three.objects import (
    Material,
    Object3D,
)
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene import Scene
from kivyfn.three.utils.color import random_color
from kivyfn.three.paths import RESOURCES_PATH


class MainApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.rotation_events: dict[Object3D, ClockEvent] = {}

    def on_start(self):

        model_path = (
            RESOURCES_PATH
            / "models"
            / "glb"
            / "dashboard.glb"
        )

        loader = GlbLoader()
        scene_asset = loader.load(model_path)

        self.scene = Scene()
        self.pending_objects = list(scene_asset.objects.items())

        # =================================== #
        # Shaders
        # =================================== #
        lambert_shader = Shader(
            name="lambert",
            path=(
                RESOURCES_PATH
                / "shaders"
                / "basic"
                / "lambert.glsl"
            ),
        )

        helper_shader = Shader(
            name="helper",
            path=(
                RESOURCES_PATH
                / "shaders"
                / "helper"
                / "unlit.glsl"
            ),
        )

        # =================================== #
        # Contexts
        # =================================== #
        self.scene.create_context(
            name="main",
            shader=lambert_shader,
        )

        self.scene.create_context(
            name="helper",
            shader=helper_shader,
        )

        # =================================== #
        # Controllers
        # =================================== #
        self.scene.attach_controller(
            InteractionController(),
        )

        self.scene.attach_controller(
            BlenderCameraControls(),
            priority=100,
        )

        # =================================== #
        # Helpers
        # =================================== #
        axis = AxisHelper()

        grid = GridHelper(
            size=100,
            divisions=100,
            material=Material(
                name="grid",
                uniforms={
                    "object_color": [
                        0.45,
                        0.45,
                        0.45,
                        1.0,
                    ],
                },
            ),
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

        # =================================== #
        # Lazy Load
        # =================================== #
        self.lazy_load_event = Clock.schedule_interval(
            self.lazy_load_next_object,
            0.1,
        )

    # =================================== #
    # Lazy Load
    # =================================== #
    def lazy_load_next_object(self, dt):
        if not self.pending_objects:
            self.lazy_load_event.cancel()
            return False

        name, asset = self.pending_objects.pop(0)

        material = Material(
            name=name,
            uniforms={
                "object_color": random_color(),
            },
        )

        object3d = Object3D(
            geometry=asset.geometry,
            material=material,
            name=name,
            transform=asset.transform.copy(),
            pickable=True,
        )

        object3d.bind(
            on_release=self.on_release,
        )

        self.scene.add(
            object3d,
            context="main",
        )

        return True

    # =================================== #
    # Interaction
    # =================================== #
    def on_release(self, instance, event):
        print("event:", event)

        self.change_color(event.node)
        self.animate_rotation(event.node)

    def change_color(self, object3d):
        object3d.material.set_uniform(
            "object_color",
            random_color(),
        )

    # =================================== #
    # Rotation Animation
    # =================================== #
    def animate_rotation(
        self,
        object3d: Object3D,
    ) -> None:

        # --- Stop rotating
        if object3d in self.rotation_events:
            event = self.rotation_events.pop(object3d)
            event.cancel()
            return

        # --- Start rotating
        event = Clock.schedule_interval(
            lambda dt: self.rotate_object(
                object3d,
                dt,
            ),
            1 / 60,
        )

        self.rotation_events[object3d] = event

    def rotate_object(
        self,
        object3d: Object3D,
        dt: float,
    ) -> None:
        object3d.rotate_by(
            angle_degrees=20 * dt,
            axis=Vector3(1, 0, 0),
        )


if __name__ == "__main__":
    MainApp().run()
