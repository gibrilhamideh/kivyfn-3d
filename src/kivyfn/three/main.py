# kivyfn/three/main.py

from __future__ import annotations

from pathlib import Path

from kivy.app import App

from kivyfn.three.math.vector import Vector3
from kivyfn.three.scene import Scene
from kivyfn.three.loaders import GlbLoader
from kivyfn.three.scene.meshnode import MeshNode
from kivyfn.three.controls.orbit import OrbitCameraController


class MainApp(App):
    def on_start(self):
        resources_path = Path(__file__).parent / "resources"

        model_path = resources_path / "models" / "glb" / "monkey.glb"
        shader_path = resources_path / "shaders" / "basic" / "lambert.glsl"

        self.scene = Scene(shader_path=shader_path)

        loader = GlbLoader()
        objects = loader.load(model_path)

        for name, mesh_data in objects.items():
            node = MeshNode(name=name, mesh_data=mesh_data)
            self.scene.root_node.add_child(node)
            print(name)

        viewport = self.root.ids.viewport  # pyright: ignore
        viewport.add_widget(self.scene)

        self.scene.render()

    def _update_camera(
        self,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
    ) -> None:
        self.scene.camera.set_look_at(eye, target, up)
        self.scene.render()

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
