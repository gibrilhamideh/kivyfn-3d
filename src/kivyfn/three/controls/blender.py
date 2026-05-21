"""
Blender-style camera controls for navigating a 3D scene.

Controls
--------
Middle Mouse Drag
    Orbit camera around target.

Shift + Middle Mouse Drag
    Pan camera locally.

Mouse Wheel
    Dolly/zoom camera toward or away from target.

Notes
-----
This controller operates on the scene's active camera and
uses OrbitCameraController internally for camera movement math.

The controller is designed to behave similarly to Blender's
viewport navigation workflow while remaining engine-agnostic.

Typical Usage
-------------
scene.attach(
    BlenderCameraControls(),
    priority=100,
)
"""

from __future__ import annotations

from kivy.core.window import Window

from kivyfn.three.controls.base import SceneController
from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.math.vector import Vector3


class BlenderCameraControls(SceneController):
    def __init__(
        self,
        orbit_sensitivity: float = 0.25,
        pan_sensitivity: float = 0.01,
        zoom_sensitivity: float = 3.0,
    ):
        super().__init__()

        self.orbit_sensitivity = orbit_sensitivity
        self.pan_sensitivity = pan_sensitivity
        self.zoom_sensitivity = zoom_sensitivity

        self._active = False
        self._mode: str | None = None
        self._last_pos: tuple[float, float] | None = None

    def on_touch_down(self, touch) -> bool:
        if self.scene is None:
            return False

        button = getattr(touch, "button", None)
        if button == "scrollup":
            self._zoom(-self.zoom_sensitivity)
            return True

        if button == "scrolldown":
            self._zoom(self.zoom_sensitivity)
            return True

        if button != "middle":
            return False

        self._active = True
        self._last_pos = touch.pos

        modifiers = Window.modifiers
        if "shift" in modifiers:
            self._mode = "pan"
        else:
            self._mode = "orbit"

        touch.grab(self.scene)
        return True

    def on_touch_move(self, touch) -> bool:
        if self.scene is None:
            return False

        if not self._active:
            return False

        if self._last_pos is None:
            self._last_pos = touch.pos
            return True

        last_x, last_y = self._last_pos
        dx = touch.x - last_x
        dy = touch.y - last_y
        self._last_pos = touch.pos

        if self._mode == "orbit":
            self._orbit(dx, dy)
            return True

        if self._mode == "pan":
            self._pan(dx, dy)
            return True

        return False

    def on_touch_up(self, touch) -> bool:
        if not self._active:
            return False

        if touch.grab_current is self.scene:
            touch.ungrab(self.scene)

        self._active = False
        self._mode = None
        self._last_pos = None

        return True

    def _orbit(self, dx: float, dy: float) -> None:
        if self.scene is None:
            return

        camera = self.scene.camera

        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=dx * self.orbit_sensitivity,
            dy=dy * self.orbit_sensitivity,
        )

        camera.set_look_at(eye, target, up)
        self.scene.render()

    def _pan(self, dx: float, dy: float) -> None:
        if self.scene is None:
            return

        camera = self.scene.camera

        eye, target, up = OrbitCameraController.move_local(
            camera.eye,
            camera.target,
            camera.up,
            Vector3(-dx, -dy, 0.0),
            self.pan_sensitivity,
        )

        camera.set_look_at(eye, target, up)
        self.scene.render()

    def _zoom(self, amount: float) -> None:
        if self.scene is None:
            return

        camera = self.scene.camera

        eye, target, up = OrbitCameraController.dolly(
            camera.eye,
            camera.target,
            camera.up,
            amount,
        )

        camera.set_look_at(eye, target, up)
        self.scene.render()
