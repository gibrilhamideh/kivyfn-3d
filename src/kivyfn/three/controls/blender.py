# kivyfn/three/controls/blender.py
"""
Blender-style camera controls for navigating a 3D scene with optional boundary clamping.

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
    BlenderCameraControls(
        min_pitch=2.0,
        max_pitch=85.0,
        min_zoom=5.0,
        max_zoom=150.0,
        min_bounds=Vector3(-100.0, 0.0, -100.0),
        max_bounds=Vector3(100.0, 30.0, 100.0),
    ),
    priority=100,
)
"""
from __future__ import annotations

from kivy.core.window import Window

from kivyfn.three.scene.scene import Scene
from kivyfn.three.views.camera import Camera
from kivyfn.three.controls.base import BaseController
from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.math.vector import Vector3


class BlenderCameraControls(BaseController):
    def __init__(
        self,
        camera: Camera,
        *,
        zoom_sensitivity: float = 3.0,
        orbit_sensitivity: float = 0.5,
        pan_sensitivity: float = 0.5,
        invert_pan_x: bool = False,
        invert_pan_y: bool = False,
        adaptive_pan: bool = True,
        min_pitch: float | None = None,
        max_pitch: float | None = None,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
        min_bounds: Vector3 | None = None,
        max_bounds: Vector3 | None = None,
    ):
        super().__init__()

        self.scene: Scene | None = None
        self.camera = camera

        self.zoom_sensitivity = zoom_sensitivity
        self.orbit_sensitivity = orbit_sensitivity
        self.pan_sensitivity = pan_sensitivity
        self.invert_pan_x = invert_pan_x
        self.invert_pan_y = invert_pan_y
        self.adaptive_pan = adaptive_pan

        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.min_bounds = min_bounds
        self.max_bounds = max_bounds

        self._active = False
        self._mode: str | None = None
        self._last_pos: tuple[float, float] | None = None


    # =================================== #
    # Events
    # =================================== #

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

    # =================================== #
    # View Controls
    # =================================== #

    def _orbit(self, dx: float, dy: float) -> None:

        position, target, up = OrbitCameraController.orbit(
            self.camera.position,
            self.camera.target,
            self.camera.up,
            dx=dx * self.orbit_sensitivity,
            dy=dy * self.orbit_sensitivity,
            min_pitch_degrees=self.min_pitch,
            max_pitch_degrees=self.max_pitch,
        )

        self.camera.set_look_at(
            position,
            target,
            up,
        )

    def _pan(self, dx: float, dy: float) -> None:
        scene = self.require_scene()
        camera = self.camera
        units_per_pixel = self.pan_sensitivity

        if self.invert_pan_x:
            dx = -dx

        if self.invert_pan_y:
            dy = -dy

        if self.adaptive_pan:
            units_per_pixel *= OrbitCameraController.adaptive_pan_units_per_pixel(
                eye=camera.position,
                target=camera.target,
                fov_y_degrees=camera.fov,
                screen_height=scene.height or 1.0,
            )

        position, target, up = OrbitCameraController.pan(
            camera.position,
            camera.target,
            camera.up,
            dx=dx,
            dy=dy,
            units_per_pixel=units_per_pixel,
            min_bounds=self.min_bounds,
            max_bounds=self.max_bounds,
        )

        camera.set_look_at(position, target, up)

    def _zoom(self, amount: float) -> None:
        camera = self.camera

        if camera.projection == "orthographic":
            camera.ortho_size = OrbitCameraController.zoom_orthographic(
                current_size=camera.ortho_size,
                dy=amount,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            return

        position, target, up = OrbitCameraController.dolly(
            camera.position,
            camera.target,
            camera.up,
            dy=amount,
            units_per_pixel=0.01,
            min_zoom=self.min_zoom,
            max_zoom=self.max_zoom,
        )

        camera.set_look_at(
            position,
            target,
            up,
        )
