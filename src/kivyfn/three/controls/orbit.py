# kivyfn/three/controls/orbit.py
from __future__ import annotations
import math
from kivyfn.three.math.vector import Vector3

class OrbitCameraController:
    EPSILON = 1e-6
    MIN_DISTANCE = 0.1

    @classmethod
    def basis(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
    ) -> tuple[Vector3, Vector3, Vector3, Vector3]:
        forward = target - eye
        if forward.length < cls.EPSILON:
            forward = Vector3(0.0, 0.0, -1.0)
            target = eye + forward
        forward = forward.normalize()
        right = forward.cross(up)
        if right.length < cls.EPSILON:
            fallback_axis = min(
                [
                    Vector3(1.0, 0.0, 0.0),
                    Vector3(0.0, 1.0, 0.0),
                    Vector3(0.0, 0.0, 1.0),
                ],
                key=lambda axis: abs(axis.dot(forward)),
            )
            right = forward.cross(fallback_axis)
        right = right.normalize()
        corrected_up = right.cross(forward).normalize()
        return forward, right, corrected_up, target

    @classmethod
    def move_local(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        local_direction: Vector3,
        step: float,
    ) -> tuple[Vector3, Vector3, Vector3]:
        forward, right, corrected_up, target = cls.basis(eye, target, up)
        movement = (
            (right * local_direction.x)
            + (corrected_up * local_direction.y)
            + (forward * local_direction.z)
        ) * step
        eye = eye + movement
        target = target + movement
        eye_to_target = target - eye
        if eye_to_target.length < cls.MIN_DISTANCE:
            target = eye + (forward.normalize() * cls.MIN_DISTANCE)
        
        return eye, target, up

    @classmethod
    def orbit(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dx: float,
        dy: float,
        degrees_per_pixel: float = 0.25,
        min_pitch_degrees: float | None = None,  # Default: No pitch constraint
        max_pitch_degrees: float | None = None,
    ) -> tuple[Vector3, Vector3, Vector3]:
        forward, right, corrected_up, target = cls.basis(eye, target, up)
        offset = eye - target

        yaw = math.radians(-dx * degrees_per_pixel)
        offset = offset.rotate(up, yaw)

        temporary_forward = (offset * -1.0).normalize()
        temporary_right = temporary_forward.cross(up)
        if temporary_right.length < cls.EPSILON:
            temporary_right = right
        temporary_right = temporary_right.normalize()

        pitch = math.radians(-dy * degrees_per_pixel)
        pitched_offset = offset.rotate(temporary_right, pitch)
        pitched_normal = pitched_offset.normalize()

        # CLAMP PITCH (If provided)
        current_sin = pitched_normal.dot(up)
        min_sin = math.sin(math.radians(min_pitch_degrees)) if min_pitch_degrees is not None else -1.0
        max_sin = math.sin(math.radians(max_pitch_degrees)) if max_pitch_degrees is not None else 1.0

        # Enforce basic gimbal lock protection if no limits given
        if min_pitch_degrees is None and max_pitch_degrees is None:
            if abs(current_sin) <= 0.98:
                offset = pitched_offset
        elif min_sin <= current_sin <= max_sin:
            offset = pitched_offset

        eye = target + offset
        return eye, target, up

    @classmethod
    def pan(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dx: float,
        dy: float,
        units_per_pixel: float = 0.003,
        min_bounds: Vector3 | None = None,  # Default: Infinite panning
        max_bounds: Vector3 | None = None,
    ) -> tuple[Vector3, Vector3, Vector3]:
        _, right, corrected_up, target = cls.basis(eye, target, up)
        delta = (
            (right * (-dx * units_per_pixel))
            + (corrected_up * (dy * units_per_pixel))
        )
        
        proposed_target = target + delta
        
        # CLAMP PAN (If bounds provided)
        if min_bounds is not None and max_bounds is not None:
            proposed_target.x = max(min_bounds.x, min(proposed_target.x, max_bounds.x))
            proposed_target.y = max(min_bounds.y, min(proposed_target.y, max_bounds.y))
            proposed_target.z = max(min_bounds.z, min(proposed_target.z, max_bounds.z))
            
        allowed_delta = proposed_target - target
        return eye + allowed_delta, proposed_target, up

    @classmethod
    def dolly(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dy: float,
        units_per_pixel: float = 0.01,
        min_zoom: float | None = None,  # Default: No zoom constraint
        max_zoom: float | None = None,
    ) -> tuple[Vector3, Vector3, Vector3]:
        forward, _, corrected_up, target = cls.basis(eye, target, up)
        current_distance = (target - eye).length
        step = dy * units_per_pixel * current_distance
        proposed_eye = eye + (forward * step)
        
        proposed_distance = (target - proposed_eye).length

        # CLAMP ZOOM (If limits provided)
        actual_min = max(min_zoom, cls.MIN_DISTANCE) if min_zoom is not None else cls.MIN_DISTANCE
        
        if max_zoom is not None:
            if actual_min <= proposed_distance <= max_zoom:
                eye = proposed_eye
        else:
            if proposed_distance >= actual_min:
                eye = proposed_eye
            
        return eye, target, up

    @classmethod
    def zoom_orthographic(
        cls,
        current_size: float,
        dy: float,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
    ) -> float:
        """Computes the new view size width for an orthographic camera matrix projection."""
        # Scale zoom step relative to current size so scrolling feels smooth
        scale_factor = current_size * 0.05
        proposed_size = current_size + (dy * scale_factor)
        
        # Enforce boundary clamp constraints safely
        actual_min = max(min_zoom, cls.MIN_DISTANCE) if min_zoom is not None else cls.MIN_DISTANCE
        
        if max_zoom is not None:
            return max(actual_min, min(proposed_size, max_zoom))
        return max(actual_min, proposed_size)

    @classmethod
    def adaptive_pan_units_per_pixel(
        cls,
        eye: Vector3,
        target: Vector3,
        fov_y_degrees: float,
        screen_height: float,
        minimum_distance: float = 0.1,
    ) -> float:
        distance = max((target - eye).length, max(minimum_distance, cls.MIN_DISTANCE))
        fov_y = math.radians(fov_y_degrees)
        half_height = distance * math.tan(fov_y / 2.0)
        height = max(screen_height, 1.0)
        return (2.0 * half_height) / height
