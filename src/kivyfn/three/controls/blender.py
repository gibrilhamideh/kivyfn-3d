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

from kivyfn.three.controls.base import SceneController
from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.math.vector import Vector3
from kivyfn.three.scene.view import View


class BlenderCameraControls(SceneController):
    def __init__(
        self,
        view_name: str = "main",
        orbit_sensitivity: float = 0.25,
        pan_sensitivity: float = 0.01,
        zoom_sensitivity: float = 3.0,
        min_pitch: float | None = None,
        max_pitch: float | None = None,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
        min_bounds: Vector3 | None = None,
        max_bounds: Vector3 | None = None,
    ):
        super().__init__()

        self.view_name = view_name

        self.orbit_sensitivity = orbit_sensitivity
        self.pan_sensitivity = pan_sensitivity
        self.zoom_sensitivity = zoom_sensitivity

        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.min_bounds = min_bounds
        self.max_bounds = max_bounds

        self._active = False
        self._mode: str | None = None
        self._last_pos: tuple[float, float] | None = None

    @property
    def view(self) -> View:
        assert self.scene is not None
        return self.scene.views[self.view_name]

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
        view = self.view

        position, target, up = OrbitCameraController.orbit(
            view.position,
            view.target,
            view.up,
            dx=dx * self.orbit_sensitivity,
            dy=dy * self.orbit_sensitivity,
            min_pitch_degrees=self.min_pitch,
            max_pitch_degrees=self.max_pitch,
        )

        view.set_look_at(
            position,
            target,
            up,
        )

    def _pan(self, dx: float, dy: float) -> None:
        view = self.view

        position, target, up = OrbitCameraController.pan(
            view.position,
            view.target,
            view.up,
            dx=dx,
            dy=dy,
            units_per_pixel=self.pan_sensitivity,
            min_bounds=self.min_bounds,
            max_bounds=self.max_bounds,
        )

        view.set_look_at(
            position,
            target,
            up,
        )

    def _zoom(self, amount: float) -> None:
        view = self.view

        if view.perspective == 0.0:
            view.ortho_size = OrbitCameraController.zoom_orthographic(
                current_size=view.ortho_size,
                dy=amount,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            return

        position, target, up = OrbitCameraController.dolly(
            view.position,
            view.target,
            view.up,
            dy=amount,
            units_per_pixel=0.01,
            min_zoom=self.min_zoom,
            max_zoom=self.max_zoom,
        )

        view.set_look_at(
            position,
            target,
            up,
        )
