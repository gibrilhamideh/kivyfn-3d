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
        forward, right, corrected_up, target = cls.basis(
            eye,
            target,
            up,
        )

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

        return eye, target, corrected_up

    @classmethod
    def orbit(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dx: float,
        dy: float,
        degrees_per_pixel: float = 0.25,
    ) -> tuple[Vector3, Vector3, Vector3]:
        forward, right, corrected_up, target = cls.basis(
            eye,
            target,
            up,
        )

        offset = eye - target

        yaw = math.radians(-dx * degrees_per_pixel)
        offset = offset.rotate(corrected_up, yaw)

        temporary_forward = (offset * -1.0).normalize()
        temporary_right = temporary_forward.cross(corrected_up)

        if temporary_right.length < cls.EPSILON:
            temporary_right = right

        temporary_right = temporary_right.normalize()

        pitch = math.radians(-dy * degrees_per_pixel)
        pitched_offset = offset.rotate(temporary_right, pitch)

        pitched_normal = pitched_offset.normalize()

        if abs(pitched_normal.dot(corrected_up)) <= 0.98:
            offset = pitched_offset

        eye = target + offset

        return eye, target, corrected_up

    @classmethod
    def pan(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dx: float,
        dy: float,
        units_per_pixel: float = 0.003,
    ) -> tuple[Vector3, Vector3, Vector3]:
        _, right, corrected_up, target = cls.basis(
            eye,
            target,
            up,
        )

        delta = (
            (right * (-dx * units_per_pixel))
            + (corrected_up * (dy * units_per_pixel))
        )

        return (
            eye + delta,
            target + delta,
            corrected_up,
        )

    @classmethod
    def dolly(
        cls,
        eye: Vector3,
        target: Vector3,
        up: Vector3,
        dy: float,
        units_per_pixel: float = 0.01,
    ) -> tuple[Vector3, Vector3, Vector3]:
        forward, _, corrected_up, target = cls.basis(
            eye,
            target,
            up,
        )

        distance = max(
            (target - eye).length,
            cls.MIN_DISTANCE,
        )

        step = dy * units_per_pixel * distance
        new_eye = eye + (forward * step)

        if (target - new_eye).length >= cls.MIN_DISTANCE:
            eye = new_eye

        return eye, target, corrected_up

    @classmethod
    def adaptive_pan_units_per_pixel(
        cls,
        eye: Vector3,
        target: Vector3,
        fov_y_degrees: float,
        screen_height: float,
        minimum_distance: float = 0.1,
    ) -> float:
        distance = max(
            (target - eye).length,
            max(minimum_distance, cls.MIN_DISTANCE),
        )

        fov_y = math.radians(fov_y_degrees)
        half_height = distance * math.tan(fov_y / 2.0)
        height = max(screen_height, 1.0)

        return (2.0 * half_height) / height
