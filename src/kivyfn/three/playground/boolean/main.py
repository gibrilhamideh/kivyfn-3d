from __future__ import annotations

from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.controls import BlenderCameraControls, InteractionController
from kivyfn.three.helpers import AxisHelper, GridHelper
from kivyfn.three.modifiers.boolean import BooleanModifier
from kivyfn.three.objects import Material
from kivyfn.three.primitives.box import Box
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene import Scene
from kivyfn.three.paths import RESOURCES_PATH


class MainApp(App):
    def on_start(self):

        self.scene = Scene()

        lambert_shader = Shader(
            name="lambert",
            path= RESOURCES_PATH / "shaders" / "basic" / "lambert.glsl",
        )

        helper_shader = Shader(
            name="helper",
            path= RESOURCES_PATH / "shaders" / "helper" / "unlit.glsl",
        )

        self.scene.create_context(
            name="main",
            shader=lambert_shader,
        )

        self.scene.create_context(
            name="helper",
            shader=helper_shader,
        )

        self.scene.attach_controller(InteractionController())

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

        self.scene.add(axis, context="helper")
        self.scene.add(grid, context="helper")

        self.root.add_widget(self.scene)  # pyright: ignore

        self.create_boolean_test()

    def create_boolean_test(self) -> None:
        wall_material = Material(
            name="wall",
            uniforms={
                "object_color": [0.75, 0.75, 0.75, 1.0],
            },
        )

        wall = Box(
            width=6.0,
            height=4.0,
            depth=1.0,
            material=wall_material,
            name="solid_box_wall",
        )

        cutter = Box(
            width=2.0,
            height=1.5,
            depth=3.0,  # longer than wall depth
            material=wall_material,
            name="box_hole_cutter",
        )

        modifier = BooleanModifier(
            cutter=cutter,
            operation="difference",
            check_volume=False,
            flat_shading=False,
            name="box_with_round_hole",
        )


        box_with_hole = modifier.apply_to_object(wall)

        self.scene.add(
            box_with_hole,
            context="main",
        )


if __name__ == "__main__":
    MainApp().run()
