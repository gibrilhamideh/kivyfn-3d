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

class BlenderCameraControls(SceneController):
    def __init__(
        self,
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
        self.orbit_sensitivity = orbit_sensitivity
        self.pan_sensitivity = pan_sensitivity
        self.zoom_sensitivity = zoom_sensitivity
        
        # Guardrail Boundaries
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
    def camera(self):
        assert self.scene is not None
        return self.scene.camera

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
    # Camera Controls
    # =================================== #
    def _orbit(self, dx: float, dy: float) -> None:
        camera = self.camera
        eye, target, up = OrbitCameraController.orbit(
            camera.eye,
            camera.target,
            camera.up,
            dx=dx * self.orbit_sensitivity,
            dy=dy * self.orbit_sensitivity,
            min_pitch_degrees=self.min_pitch,
            max_pitch_degrees=self.max_pitch,
        )
        camera.set_look_at(eye, target, up)

    def _pan(self, dx: float, dy: float) -> None:
        camera = self.camera
        eye, target, up = OrbitCameraController.pan(
            camera.eye,
            camera.target,
            camera.up,
            dx=dx,
            dy=dy,
            units_per_pixel=self.pan_sensitivity,
            min_bounds=self.min_bounds,
            max_bounds=self.max_bounds,
        )
        camera.set_look_at(eye, target, up)

    def _zoom(self, amount: float) -> None:
        camera = self.camera

        # 1. ORTHOGRAPHIC PROJECTION TYPE
        if getattr(camera, "perspective", 1.0) == 0.0:
            camera.ortho_size = OrbitCameraController.zoom_orthographic(
                current_size=camera.ortho_size,
                dy=amount,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )

        # 2. PERSPECTIVE PROJECTION TYPE
        else:
            eye, target, up = OrbitCameraController.dolly(
                camera.eye,
                camera.target,
                camera.up,
                dy=amount,
                units_per_pixel=0.01,
                min_zoom=self.min_zoom,
                max_zoom=self.max_zoom,
            )
            camera.set_look_at(eye, target, up)
