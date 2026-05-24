# kivyfn/three/playground/boolean/main.py
from __future__ import annotations

from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App

from kivyfn.three.math.vector import Vector3
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.controls import BlenderCameraControls, InteractionController
from kivyfn.three.helpers import AxisHelper, GridHelper
from kivyfn.three.modifiers.boolean import BooleanModifier
from kivyfn.three.objects import Material
from kivyfn.three.primitives import Box, Cube, Cylinder, Sphere
from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.scene import Scene
from kivyfn.three.paths import RESOURCES_PATH


class MainApp(App):
    def on_start(self) -> None:
        self.scene = Scene()

        lambert_shader = Shader(
            name="lambert",
            path=RESOURCES_PATH / "shaders" / "basic" / "lambert.glsl",
        )

        helper_shader = Shader(
            name="helper",
            path=RESOURCES_PATH / "shaders" / "helper" / "unlit.glsl",
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
                base_color=[0.45, 0.45, 0.45, 1.0],
            ),
        )

        self.scene.add(axis, context="helper")
        self.scene.add(grid, context="helper")

        self.root.add_widget(self.scene)  # pyright: ignore

        # Pick one test at a time.
        # self.test_box_difference_box()
        self.test_box_difference_cylinder()
        # self.test_cube_union_sphere()
        # self.test_sphere_intersection_box()
        # self.test_box_difference_sphere()

    # =================================== #
    # Materials
    # =================================== #
    def make_material(
        self,
        name: str,
        color: list[float],
    ) -> Material:
        return Material(
            name=name,
            base_color=color,
        )

    # =================================== #
    # Test 1: Difference
    # Box - Box
    # =================================== #
    def test_box_difference_box(self) -> None:
        material = self.make_material(
            name="box_difference_box_material",
            color=[0.75, 0.75, 0.75, 1.0],
        )

        wall = Box(
            width=6.0,
            height=4.0,
            depth=1.0,
            material=material,
            name="difference_wall",
        )

        cutter = Box(
            width=2.0,
            height=1.5,
            depth=3.0,
            material=material,
            name="box_cutter",
        )

        modifier = BooleanModifier(
            cutter=cutter,
            operation="difference",
            check_volume=False,
            flat_shading=True,
            name="box_difference_box_result",
        )

        result = modifier.apply_to_object(wall)

        self.scene.add(
            result,
            context="main",
        )

    # =================================== #
    # Test 2: Difference
    # Box - Cylinder
    # =================================== #
    def test_box_difference_cylinder(self) -> None:
        material = self.make_material(
            name="box_difference_cylinder_material",
            color=[0.9, 0.25, 0.2, 1.0],
        )

        wall = Box(
            width=6.0,
            height=4.0,
            depth=1.0,
            material=material,
            name="round_hole_wall",
        )

        cutter = Cylinder(
            radius=0.8,
            height=3.0,
            segments=48,
            material=material,
            name="cylinder_cutter",
        )

        cutter.transform.translation = Vector3(
            0.0,
            0.0,
            0.0,
        )

        cutter.transform.rotation = Quaternion.from_axis_angle(
            Vector3(1.0, 0.0, 0.0),
            90.0,
        )

        modifier = BooleanModifier(
            cutter=cutter,
            operation="difference",
            check_volume=False,
            flat_shading=True,
            name="box_difference_cylinder_result",
        )

        result = modifier.apply_to_object(wall)

        self.scene.add(
            result,
            context="main",
        )


    # =================================== #
    # Test 3: Union
    # Cube + Sphere
    # =================================== #
    def test_box_difference_sphere(self) -> None:
        material = self.make_material(
            name="box_difference_sphere_material",
            color=[0.9, 0.25, 0.2, 1.0],
        )

        wall = Box(
            width=6.0,
            height=4.0,
            depth=1.0,
            material=material,
            name="sphere_hole_wall",
        )

        cutter = Sphere(
            radius=0.9,
            segments=32,
            rings=16,
            material=material,
            name="sphere_cutter",
        )

        print("wall stats:", wall.geometry.get_stats())
        print("sphere stats:", cutter.geometry.get_stats())

        modifier = BooleanModifier(
            cutter=cutter,
            operation="difference",
            check_volume=False,
            flat_shading=True,
            name="box_difference_sphere_result",
        )

        result = modifier.apply_to_object(wall)

        self.scene.add(
            result,
            context="main",
        )

    # =================================== #
    # Test 3: Union
    # Cube + Sphere
    # =================================== #
    def test_cube_union_sphere(self) -> None:
        material = self.make_material(
            name="cube_union_sphere_material",
            color=[0.25, 0.8, 0.35, 1.0],
        )

        cube = Cube(
            size=2.0,
            material=material,
            name="union_cube",
        )

        sphere = Sphere(
            radius=1.25,
            segments=32,
            rings=16,
            material=material,
            name="union_sphere",
        )

        sphere.transform.translation = Vector3(0.9, 0.0, 0.0)

        modifier = BooleanModifier(
            cutter=sphere,
            operation="union",
            check_volume=False,
            flat_shading=True,
            name="cube_union_sphere_result",
        )

        result = modifier.apply_to_object(cube)

        self.scene.add(
            result,
            context="main",
        )

    # =================================== #
    # Test 4: Intersection
    # Sphere ∩ Box
    # =================================== #
    def test_sphere_intersection_box(self) -> None:
        material = self.make_material(
            name="sphere_intersection_box_material",
            color=[0.25, 0.45, 0.9, 1.0],
        )

        sphere = Sphere(
            radius=1.6,
            segments=32,
            rings=16,
            material=material,
            name="intersection_sphere",
        )

        box = Box(
            width=2.4,
            height=2.4,
            depth=2.4,
            material=material,
            name="intersection_box",
        )

        box.transform.translation = Vector3(0.8, 0.0, 0.0)

        modifier = BooleanModifier(
            cutter=box,
            operation="intersection",
            check_volume=False,
            flat_shading=True,
            name="sphere_intersection_box_result",
        )

        result = modifier.apply_to_object(sphere)

        self.scene.add(
            result,
            context="main",
        )


if __name__ == "__main__":
    MainApp().run()
