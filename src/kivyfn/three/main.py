# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.app import App
from kivy.clock import Clock

from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3
from kivyfn.three.scene import Scene
from kivyfn.three.scene.meshnode import MeshNode


class MainApp(App):
    def on_start(self):
        resources_path = Path(__file__).parent / "resources"

        model_path = resources_path / "models" / "glb" / "monkey.glb"
        shader_path = resources_path / "shaders" / "basic" / "lambert.glsl"

        self.scene = Scene(shader_path=shader_path)
        self.monkey_nodes: list[MeshNode] = []
        self.monkey_angle = 0.0
        self.monkey_rotating = False

        loader = GlbLoader()
        objects = loader.load(model_path)

        self.monkey = None
        for name, mesh_data in objects.items():
            node = MeshNode(name=name, mesh_data=mesh_data)
            self.monkey = node
            self.scene.root_node.add_child(node)
            self.monkey_nodes.append(node)

        self.monkey.bind(on_press=self.on_test) # pyright: ignore

        viewport = self.root.ids.viewport  # pyright: ignore
        viewport.add_widget(self.scene)

        self.scene.render()

    _counter = 0
    def on_test(self, instance, event):
        print("hit: ", self._counter)
        self._counter += 1

    def _update_camera(
        self,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
    ) -> None:
        self.scene.camera.set_look_at(eye, target, up)
        self.scene.render()

    def _set_monkey_rotation(self, angle: float) -> None:
        self.monkey_angle = angle

        rotation = Quaternion.from_axis_angle(
            Vector3(0.0, 1.0, 0.0),
            self.monkey_angle,
        )

        for node in self.monkey_nodes:
            node.transform.rotation = rotation

        self.scene.render()

    def rotate_monkey_left(self):
        self._set_monkey_rotation(self.monkey_angle - 15.0)

    def rotate_monkey_right(self):
        self._set_monkey_rotation(self.monkey_angle + 15.0)

    def toggle_monkey_rotation(self):
        self.monkey_rotating = not self.monkey_rotating

        if self.monkey_rotating:
            Clock.schedule_interval(self._animate_monkey_rotation, 1 / 60)
        else:
            Clock.unschedule(self._animate_monkey_rotation)

    def _animate_monkey_rotation(self, dt: float):
        self._set_monkey_rotation(self.monkey_angle + (dt * 90.0))

    def pan_left(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.move_local(
            camera.eye,
            camera.target,
            camera.up,
            Vector3(-1.0, 0.0, 0.0),
            0.4,
        )
        self._update_camera(eye, target, up)

    def pan_right(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.move_local(
            camera.eye,
            camera.target,
            camera.up,
            Vector3(1.0, 0.0, 0.0),
            0.4,
        )
        self._update_camera(eye, target, up)

    def pan_up(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.move_local(
            camera.eye,
            camera.target,
            camera.up,
            Vector3(0.0, 1.0, 0.0),
            0.4,
        )
        self._update_camera(eye, target, up)

    def pan_down(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.move_local(
            camera.eye,
            camera.target,
            camera.up,
            Vector3(0.0, -1.0, 0.0),
            0.4,
        )
        self._update_camera(eye, target, up)

    def zoom_out(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.dolly(
            camera.eye,
            camera.target,
            camera.up,
            -20.0,
        )
        self._update_camera(eye, target, up)

    def zoom_in(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.dolly(
            camera.eye,
            camera.target,
            camera.up,
            20.0,
        )
        self._update_camera(eye, target, up)

    def orbit_left(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=-20.0,
            dy=0.0,
        )
        self._update_camera(eye, target, up)

    def orbit_right(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=20.0,
            dy=0.0,
        )
        self._update_camera(eye, target, up)

    def orbit_up(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=0.0,
            dy=-20.0,
        )
        self._update_camera(eye, target, up)

    def orbit_down(self):
        camera = self.scene.camera
        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=0.0,
            dy=20.0,
        )
        self._update_camera(eye, target, up)


if __name__ == "__main__":
    MainApp().run()
