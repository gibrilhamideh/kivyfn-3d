# kivyfn/three/controls/touch.py

"""
Production touch camera controls.

Controls
--------
One finger drag:
    Orbit camera around target.

Two finger drag:
    Pan camera.

Two finger pinch:
    Zoom in/out.

Notes
-----
This class is intentionally NOT using kivy.gesture.Gesture.
kivy.gesture is for recognizing drawn shapes/patterns.
Camera navigation needs continuous multitouch tracking instead.
"""



from __future__ import annotations
from typing import TYPE_CHECKING

import math
from dataclasses import dataclass

from kivyfn.three.controls.base import BaseController
from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.math.vector import Vector3
from kivyfn.three.views import camera
from kivyfn.three.views.camera import Camera

if TYPE_CHECKING:
    from kivyfn.three.views.view import View


@dataclass(slots=True)
class TouchPoint:
    uid: object
    x: float
    y: float

    @property
    def pos(self) -> tuple[float, float]:
        return self.x, self.y


class TouchCameraControls(BaseController):
    MODE_IDLE = "idle"
    MODE_ORBIT_PENDING = "orbit_pending"
    MODE_ORBIT = "orbit"
    MODE_TWO_PENDING = "two_pending"
    MODE_TWO = "two"

    def __init__(
        self,
        camera: Camera,
        *,
        zoom_sensitivity: float = 0.20,
        orbit_sensitivity: float = 0.75,
        pan_sensitivity: float = 0.75,
        invert_pan_x: bool = False,
        invert_pan_y: bool = False,
        adaptive_pan: bool = True,
        orbit_deadzone: float = 2.0,
        pan_deadzone: float = 1.5,
        pinch_deadzone: float = 1.5,
        smoothing: float = 0.35,
        accept_mouse: bool = False,
        min_pitch: float | None = None,
        max_pitch: float | None = None,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
        min_bounds: Vector3 | None = None,
        max_bounds: Vector3 | None = None,
    ):
        super().__init__()

        self.camera = camera

        self.zoom_sensitivity = zoom_sensitivity
        self.orbit_sensitivity = orbit_sensitivity
        self.pan_sensitivity = pan_sensitivity
        self.invert_pan_x = invert_pan_x
        self.invert_pan_y = invert_pan_y
        self.adaptive_pan = adaptive_pan

        self.orbit_deadzone = orbit_deadzone
        self.pan_deadzone = pan_deadzone
        self.pinch_deadzone = pinch_deadzone
        self.smoothing = max(0.0, min(smoothing, 1.0))

        self.accept_mouse = accept_mouse

        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.min_bounds = min_bounds
        self.max_bounds = max_bounds

        self._points: dict[object, TouchPoint] = {}

        self._mode = self.MODE_IDLE

        self._last_single_pos: tuple[float, float] | None = None

        self._last_two_center: tuple[float, float] | None = None
        self._last_two_distance: float | None = None

        self._smooth_orbit_dx = 0.0
        self._smooth_orbit_dy = 0.0

        self._smooth_pan_dx = 0.0
        self._smooth_pan_dy = 0.0
        self._smooth_pinch_delta = 0.0

        self._suppress_single_until_release = False


    # =================================== #
    # Events
    # =================================== #

    def on_touch_down(self, touch) -> bool:
        if self.scene is None:
            return False

        if not self._accept_touch(touch):
            return False

        if len(self._points) >= 2:
            return False

        self._points[touch.uid] = self._make_point(touch)
        touch.grab(self.scene)

        if len(self._points) == 1:
            if self._suppress_single_until_release:
                self._mode = self.MODE_IDLE
                return True

            point = self._only_point()
            self._last_single_pos = point.pos
            self._mode = self.MODE_ORBIT_PENDING
            return True

        if len(self._points) == 2:
            self._begin_two_finger_gesture()
            return True

        return True

    def on_touch_move(self, touch) -> bool:
        if self.scene is None:
            return False

        if touch.uid not in self._points:
            return False

        self._points[touch.uid] = self._make_point(touch)

        if len(self._points) == 1:
            if self._suppress_single_until_release:
                return True

            self._handle_one_finger()
            return True

        if len(self._points) == 2:
            self._handle_two_finger()
            return True

        return True

    def on_touch_up(self, touch) -> bool:
        if touch.uid not in self._points:
            return False

        was_two_finger = len(self._points) == 2

        self._points.pop(touch.uid, None)

        if touch.grab_current is self.scene:
            touch.ungrab(self.scene)

        if len(self._points) == 0:
            self._reset_all()
            return True

        if was_two_finger and len(self._points) == 1:
            self._suppress_single_until_release = True
            self._mode = self.MODE_IDLE
            self._last_single_pos = self._only_point().pos
            return True

        return True

    # =================================== #
    # Gesture Handling
    # =================================== #

    def _handle_one_finger(self) -> None:
        point = self._only_point()

        if self._last_single_pos is None:
            self._last_single_pos = point.pos
            return

        last_x, last_y = self._last_single_pos
        dx = point.x - last_x
        dy = point.y - last_y

        distance = math.hypot(dx, dy)

        if self._mode == self.MODE_ORBIT_PENDING:
            if distance < self.orbit_deadzone:
                return

            self._mode = self.MODE_ORBIT
            self._last_single_pos = point.pos
            self._smooth_orbit_dx = 0.0
            self._smooth_orbit_dy = 0.0
            return

        self._last_single_pos = point.pos

        if self._mode != self.MODE_ORBIT:
            return

        dx, dy = self._smooth_pair(
            dx,
            dy,
            "_smooth_orbit_dx",
            "_smooth_orbit_dy",
        )

        self._orbit(dx, dy)

    def _begin_two_finger_gesture(self) -> None:
        center = self._two_center()
        distance = self._two_distance()

        self._mode = self.MODE_TWO_PENDING
        self._last_two_center = center
        self._last_two_distance = distance

        self._smooth_pan_dx = 0.0
        self._smooth_pan_dy = 0.0
        self._smooth_pinch_delta = 0.0

        self._last_single_pos = None
        self._suppress_single_until_release = True

    def _handle_two_finger(self) -> None:
        center = self._two_center()
        distance = self._two_distance()

        if self._last_two_center is None or self._last_two_distance is None:
            self._last_two_center = center
            self._last_two_distance = distance
            return

        last_center_x, last_center_y = self._last_two_center

        pan_dx = center[0] - last_center_x
        pan_dy = center[1] - last_center_y
        pinch_delta = distance - self._last_two_distance

        pan_distance = math.hypot(pan_dx, pan_dy)
        pinch_distance = abs(pinch_delta)

        if self._mode == self.MODE_TWO_PENDING:
            if (
                pan_distance < self.pan_deadzone
                and pinch_distance < self.pinch_deadzone
            ):
                return

            self._mode = self.MODE_TWO
            self._last_two_center = center
            self._last_two_distance = distance
            return

        self._last_two_center = center
        self._last_two_distance = distance

        if self._mode != self.MODE_TWO:
            return

        if pan_distance >= self.pan_deadzone:
            pan_dx, pan_dy = self._smooth_pair(
                pan_dx,
                pan_dy,
                "_smooth_pan_dx",
                "_smooth_pan_dy",
            )
            self._pan(pan_dx, pan_dy)

        if pinch_distance >= self.pinch_deadzone:
            pinch_delta = self._smooth_value(
                pinch_delta,
                "_smooth_pinch_delta",
            )
            self._zoom(pinch_delta * self.zoom_sensitivity)

    # =================================== #
    # View Controls
    # =================================== #

    def _orbit(self, dx: float, dy: float) -> None:
        camera = self.camera

        position, target, up = OrbitCameraController.orbit(
            camera.position,
            camera.target,
            camera.up,
            dx=dx * self.orbit_sensitivity,
            dy=dy * self.orbit_sensitivity,
            min_pitch_degrees=self.min_pitch,
            max_pitch_degrees=self.max_pitch,
        )

        camera.set_look_at(position, target, up)

    def _pan(self, dx: float, dy: float) -> None:
        camera = self.camera
        scene = self.require_scene()
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

        camera.set_look_at(position, target, up)

    # =================================== #
    # Touch Helpers
    # =================================== #

    def _accept_touch(self, touch) -> bool:
        button = getattr(touch, "button", None)

        if button is None:
            return True

        if self.accept_mouse and button == "left":
            return True

        return False

    def _make_point(self, touch) -> TouchPoint:
        return TouchPoint(
            uid=touch.uid,
            x=float(touch.x),
            y=float(touch.y),
        )

    def _only_point(self) -> TouchPoint:
        return next(iter(self._points.values()))

    def _two_points(self) -> tuple[TouchPoint, TouchPoint]:
        points = list(self._points.values())
        return points[0], points[1]

    def _two_center(self) -> tuple[float, float]:
        a, b = self._two_points()

        return (
            (a.x + b.x) * 0.5,
            (a.y + b.y) * 0.5,
        )

    def _two_distance(self) -> float:
        a, b = self._two_points()

        return math.hypot(
            b.x - a.x,
            b.y - a.y,
        )

    # =================================== #
    # Smoothing
    # =================================== #

    def _smooth_pair(
        self,
        x: float,
        y: float,
        attr_x: str,
        attr_y: str,
    ) -> tuple[float, float]:
        alpha = self.smoothing

        old_x = getattr(self, attr_x)
        old_y = getattr(self, attr_y)

        new_x = (old_x * (1.0 - alpha)) + (x * alpha)
        new_y = (old_y * (1.0 - alpha)) + (y * alpha)

        setattr(self, attr_x, new_x)
        setattr(self, attr_y, new_y)

        return new_x, new_y

    def _smooth_value(
        self,
        value: float,
        attr: str,
    ) -> float:
        alpha = self.smoothing

        old_value = getattr(self, attr)
        new_value = (old_value * (1.0 - alpha)) + (value * alpha)

        setattr(self, attr, new_value)

        return new_value

    # =================================== #
    # Reset
    # =================================== #

    def _reset_all(self) -> None:
        self._points.clear()

        self._mode = self.MODE_IDLE

        self._last_single_pos = None
        self._last_two_center = None
        self._last_two_distance = None

        self._smooth_orbit_dx = 0.0
        self._smooth_orbit_dy = 0.0

        self._smooth_pan_dx = 0.0
        self._smooth_pan_dy = 0.0
        self._smooth_pinch_delta = 0.0

        self._suppress_single_until_release = False
