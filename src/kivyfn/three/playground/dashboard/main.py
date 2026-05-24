# kivyfn/three/playground/dashboard/main.py

from __future__ import annotations

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
from kivyfn.three.paths import RESOURCES_PATH
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.scene import Scene
from kivyfn.three.scene.node import Node3D
from kivyfn.three.utils.color import random_color
from kivyfn.three.utils.stopwatch import Stopwatch


class MainApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.rotation_events: dict[Node3D, ClockEvent] = {}

        self.fan_node: Node3D | None = None
        self.fan_blades_node: Node3D | None = None

        self.shutters: list[Node3D] = []
        self.shutter_angles: dict[Node3D, float] = {}
        self.shutter_directions: dict[Node3D, int] = {}

    def on_start(self):

        model_path = (
            RESOURCES_PATH
            / "models"
            / "glb"
            / "Fan.glb"
        )

        with Stopwatch.section("Loader"):
            loader = GlbLoader()
            scene_asset = loader.load(model_path)

        fan_asset = scene_asset.objects.get("Fan")

        if fan_asset is None:
            raise RuntimeError(
                "Fan root object was not found in Fan.glb. "
                "Make sure the root Empty in Blender is named 'Fan'."
            )

        self.scene = Scene()

        standard_shader = Shader(
            name="standard",
            path=(
                RESOURCES_PATH
                / "shaders"
                / "basic"
                / "standard.glsl"
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

        fan_node = self.scene.load_asset(
            fan_asset,
            context="main",
            pickable=True,
        )

        self.collect_nodes(fan_node)
        self.start_fan_animation()

    def collect_nodes(
        self,
        node: Node3D,
    ) -> None:

        if node.name == "Fan":
            self.fan_node = node

        elif node.name == "FanBlades":
            self.fan_blades_node = node

        elif node.name.startswith("Shutter."):
            self.shutters.append(node)

        if isinstance(node, Object3D):
            node.bind(
                on_release=self.on_release,
            )

        for child in node.children:
            self.collect_nodes(child)

    def start_fan_animation(self) -> None:

        if self.fan_blades_node is not None:
            self.start_rotation(
                node=self.fan_blades_node,
                speed=720,
                axis=Vector3(0, 0, 1),
            )

        if self.fan_node is not None:
            self.start_rotation(
                node=self.fan_node,
                speed=30,
                axis=Vector3(0, 1, 0),
            )

        self.animate_shutters()

    def on_release(self, instance, event):

        print("event:", event)

        object3d = event.target
        self.change_color(object3d)

    def change_color(
        self,
        object3d: Object3D,
    ) -> None:
        object3d.material.base_color = random_color()

    def start_rotation(
        self,
        node: Node3D,
        speed: float,
        axis: Vector3,
    ) -> None:

        if node in self.rotation_events:
            return

        event = Clock.schedule_interval(
            lambda dt: self.rotate_node(
                node=node,
                dt=dt,
                speed=speed,
                axis=axis,
            ),
            1 / 60,
        )

        self.rotation_events[node] = event

    def rotate_node(
        self,
        node: Node3D,
        dt: float,
        speed: float,
        axis: Vector3,
    ) -> None:

        node.rotate_by(
            angle_degrees=speed * dt,
            axis=axis,
        )

    def animate_shutters(self) -> None:

        for shutter in self.shutters:
            self.start_shutter_animation(shutter)

    def start_shutter_animation(
        self,
        shutter: Node3D,
    ) -> None:

        self.shutter_angles[shutter] = 0.0
        self.shutter_directions[shutter] = 1

        Clock.schedule_interval(
            lambda dt: self.rotate_shutter(
                shutter=shutter,
                dt=dt,
                max_angle=90.0,
                speed=120.0,
                axis=Vector3(1, 0, 0),
            ),
            1 / 60,
        )

    def rotate_shutter(
        self,
        shutter: Node3D,
        dt: float,
        max_angle: float,
        speed: float,
        axis: Vector3,
    ) -> bool:

        current_angle = self.shutter_angles.get(
            shutter,
            0.0,
        )

        direction = self.shutter_directions.get(
            shutter,
            1,
        )

        step = speed * dt * direction
        next_angle = current_angle + step

        if next_angle >= max_angle:
            step = max_angle - current_angle
            next_angle = max_angle
            self.shutter_directions[shutter] = -1

        elif next_angle <= 0:
            step = -current_angle
            next_angle = 0.0
            self.shutter_directions[shutter] = 1

        shutter.rotate_by(
            angle_degrees=step,
            axis=axis,
        )

        self.shutter_angles[shutter] = next_angle

        return True


if __name__ == "__main__":
    MainApp().run()
