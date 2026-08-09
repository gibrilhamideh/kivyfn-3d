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

import math
from dataclasses import dataclass

from kivy.input.motionevent import MotionEvent
from kivy.input.providers.mouse import MouseMotionEvent

from kivyfn.three.controls.base import BaseController
from kivyfn.three.controls.orbit import OrbitCameraController
from kivyfn.three.math.vector import Vector3
from kivyfn.three.views.camera import Camera



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
    MODE_TWO_PAN = "two_pan"
    MODE_TWO_ZOOM = "two_zoom"
    MODE_TWO_COMBINED = "two_combined"

    def __init__(
        self,
        camera: Camera,
        *,
        pan_zoom_threshold: float = 8.0,
        zoom_pan_threshold: float = 6.0,
        gesture_dominance: float = 1.25,
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

        self.pan_zoom_threshold = max(float(pan_zoom_threshold), 0.0)
        self.zoom_pan_threshold = max(float(zoom_pan_threshold), 0.0)
        self.gesture_dominance = max(float(gesture_dominance), 1.0)

        self._last_two_center: tuple[float, float] | None = None
        self._last_two_distance: float | None = None

        self._locked_two_center: tuple[float, float] | None = None
        self._locked_two_distance: float | None = None

        self._points: dict[object, TouchPoint] = {}

        self._mode = self.MODE_IDLE

        self._last_single_pos: tuple[float, float] | None = None

        self._touches: dict[object, MotionEvent] = {}

        self._smooth_orbit_dx = 0.0
        self._smooth_orbit_dy = 0.0

        self._smooth_pan_dx = 0.0
        self._smooth_pan_dy = 0.0
        self._smooth_pinch_delta = 0.0

        self._initial_two_center: tuple[float, float] | None = None
        self._initial_two_distance: float | None = None

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
        self._touches[touch.uid] = touch

        touch.ud["scene_camera_gesture"] = False

        if len(self._points) == 1:
            if self._suppress_single_until_release:
                self._mode = self.MODE_IDLE
                return False

            point = self._only_point()

            self._last_single_pos = point.pos
            self._mode = self.MODE_ORBIT_PENDING

            return False

        self._mark_camera_gesture()
        self._begin_two_finger_gesture()

        for active_touch in self._touches.values():
            if active_touch.grab_current is not self.scene:
                active_touch.grab(self.scene)

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

            was_pending = self._mode == self.MODE_ORBIT_PENDING

            self._handle_one_finger()

            if (
                was_pending
                and self._mode == self.MODE_ORBIT
            ):
                self._mark_camera_gesture()

                if touch.grab_current is not self.scene:
                    touch.grab(self.scene)

            return self._mode == self.MODE_ORBIT

        if len(self._points) == 2:
            self._mark_camera_gesture()
            self._handle_two_finger()
            return True

        return False


    def on_touch_up(self, touch) -> bool:
        if touch.uid not in self._points:
            return False

        camera_gesture = bool(
            touch.ud.get(
                "scene_camera_gesture",
                False,
            )
        )

        was_two_finger = len(self._points) == 2

        self._points.pop(touch.uid, None)
        self._touches.pop(touch.uid, None)

        if touch.grab_current is self.scene:
            touch.ungrab(self.scene)

        if len(self._points) == 0:
            self._reset_all()
            return camera_gesture

        if was_two_finger and len(self._points) == 1:
            self._suppress_single_until_release = True
            self._mode = self.MODE_IDLE
            self._last_single_pos = self._only_point().pos
            return True

        return camera_gesture

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

        self._initial_two_center = center
        self._initial_two_distance = distance

        self._locked_two_center = None
        self._locked_two_distance = None

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

        if (
            self._last_two_center is None
            or self._last_two_distance is None
            or self._initial_two_center is None
            or self._initial_two_distance is None
        ):
            self._initial_two_center = center
            self._initial_two_distance = distance
            self._last_two_center = center
            self._last_two_distance = distance
            return

        last_center_x, last_center_y = self._last_two_center

        pan_dx = center[0] - last_center_x
        pan_dy = center[1] - last_center_y
        pinch_delta = distance - self._last_two_distance

        initial_center_x, initial_center_y = self._initial_two_center

        total_pan_distance = math.hypot(
            center[0] - initial_center_x,
            center[1] - initial_center_y,
        )

        total_pinch_distance = abs(
            distance - self._initial_two_distance
        )

        self._last_two_center = center
        self._last_two_distance = distance

        if self._mode == self.MODE_TWO_PENDING:
            pan_ready = total_pan_distance >= self.pan_deadzone
            zoom_ready = total_pinch_distance >= self.pinch_deadzone

            if not pan_ready and not zoom_ready:
                return

            pan_dominates = (
                pan_ready
                and total_pan_distance
                >= total_pinch_distance * self.gesture_dominance
            )

            zoom_dominates = (
                zoom_ready
                and total_pinch_distance
                >= total_pan_distance * self.gesture_dominance
            )

            if pan_dominates:
                self._mode = self.MODE_TWO_PAN

            elif zoom_dominates:
                self._mode = self.MODE_TWO_ZOOM

            elif pan_ready and not zoom_ready:
                self._mode = self.MODE_TWO_PAN

            elif zoom_ready and not pan_ready:
                self._mode = self.MODE_TWO_ZOOM

            else:
                return

            self._locked_two_center = center
            self._locked_two_distance = distance

            self._smooth_pan_dx = 0.0
            self._smooth_pan_dy = 0.0
            self._smooth_pinch_delta = 0.0
            return

        if self._mode == self.MODE_TWO_PAN:
            if self._locked_two_distance is not None:
                secondary_pinch = abs(
                    distance - self._locked_two_distance
                )

                if secondary_pinch >= self.pan_zoom_threshold:
                    self._mode = self.MODE_TWO_COMBINED

            self._apply_pan(pan_dx, pan_dy)

            if self._mode == self.MODE_TWO_COMBINED:
                self._apply_pinch(pinch_delta)

            return

        if self._mode == self.MODE_TWO_ZOOM:
            if self._locked_two_center is not None:
                locked_x, locked_y = self._locked_two_center

                secondary_pan = math.hypot(
                    center[0] - locked_x,
                    center[1] - locked_y,
                )

                if secondary_pan >= self.zoom_pan_threshold:
                    self._mode = self.MODE_TWO_COMBINED

            self._apply_pinch(pinch_delta)

            if self._mode == self.MODE_TWO_COMBINED:
                self._apply_pan(pan_dx, pan_dy)

            return

        if self._mode == self.MODE_TWO_COMBINED:
            self._apply_pan(pan_dx, pan_dy)
            self._apply_pinch(pinch_delta)

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
    def _accept_touch(self, touch: MotionEvent) -> bool:
        if not isinstance(touch, MouseMotionEvent):
            return True

        button = getattr(touch, "button", None)

        return self.accept_mouse and button == "left"


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


    def _mark_camera_gesture(self) -> None:
        for touch in self._touches.values():
            touch.ud["scene_camera_gesture"] = True

    def _apply_pan(self, dx: float, dy: float) -> None:
        if math.hypot(dx, dy) < self.pan_deadzone:
            return

        dx, dy = self._smooth_pair(
            dx,
            dy,
            "_smooth_pan_dx",
            "_smooth_pan_dy",
        )

        self._pan(dx, dy)

    def _apply_pinch(self, delta: float) -> None:
        if abs(delta) < self.pinch_deadzone:
            return

        delta = self._smooth_value(
            delta,
            "_smooth_pinch_delta",
        )

        self._zoom(
            delta * self.zoom_sensitivity
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
        self._touches.clear()

        self._mode = self.MODE_IDLE

        self._last_single_pos = None

        self._initial_two_center = None
        self._initial_two_distance = None

        self._locked_two_center = None
        self._locked_two_distance = None

        self._last_two_center = None
        self._last_two_distance = None

        self._smooth_orbit_dx = 0.0
        self._smooth_orbit_dy = 0.0

        self._smooth_pan_dx = 0.0
        self._smooth_pan_dy = 0.0
        self._smooth_pinch_delta = 0.0

        self._suppress_single_until_release = False
