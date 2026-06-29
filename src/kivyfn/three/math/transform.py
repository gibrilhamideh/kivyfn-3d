# kivyfn/three/math/transform.py

from __future__ import annotations

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.vector import Vector3


class Transform:
    __slots__ = (
        "translation",
        "rotation",
        "scale",
        "matrix",
    )

    def __init__(
        self,
        translation: Vector3 | None = None,
        rotation: Quaternion | None = None,
        scale: Vector3 | None = None,
    ) -> None:
        self.translation = Vector3(0.0, 0.0, 0.0)
        self.rotation = Quaternion.identity()
        self.scale = Vector3(1.0, 1.0, 1.0)

        # Permanent matrix object.
        # Its identity should not change.
        # Only its values are mutated.
        self.matrix = Matrix4.empty()

        self._write_full_matrix()

        if translation is not None:
            self.set_translation(translation)

        if rotation is not None:
            self.set_rotation(rotation)

        if scale is not None:
            self.set_scale(scale)

    def __repr__(
        self,
    ) -> str:
        return (
            "Transform(\n"
            f"  translation={self.translation},\n"
            f"  rotation={self.rotation},\n"
            f"  scale={self.scale}\n"
            ")"
        )

    def copy(
        self,
    ) -> Transform:
        return Transform(
            translation=self.translation.copy(),
            rotation=self.rotation.copy(),
            scale=self.scale.copy(),
        )

    # =================================== #
    # Translation
    # =================================== #

    def set_translation(
        self,
        translation: Vector3,
    ) -> None:
        self.translation.x = translation.x
        self.translation.y = translation.y
        self.translation.z = translation.z

        values = self.matrix.values
        values[0, 3] = translation.x
        values[1, 3] = translation.y
        values[2, 3] = translation.z

    def translate_by(
        self,
        offset: Vector3,
    ) -> None:
        self.translation.x += offset.x
        self.translation.y += offset.y
        self.translation.z += offset.z

        values = self.matrix.values
        values[0, 3] = self.translation.x
        values[1, 3] = self.translation.y
        values[2, 3] = self.translation.z

    # =================================== #
    # Scale
    # =================================== #

    def set_scale(
        self,
        scale: Vector3,
    ) -> None:
        self.scale.x = scale.x
        self.scale.y = scale.y
        self.scale.z = scale.z

        self._write_linear_matrix()

    def scale_by(
        self,
        factor: Vector3,
    ) -> None:
        self.scale.x *= factor.x
        self.scale.y *= factor.y
        self.scale.z *= factor.z

        self._write_linear_matrix()

    # =================================== #
    # Rotation
    # =================================== #

    def set_rotation(
        self,
        rotation: Quaternion,
    ) -> None:
        normalized = rotation.normalize()

        self.rotation.x = normalized.x
        self.rotation.y = normalized.y
        self.rotation.z = normalized.z
        self.rotation.w = normalized.w

        self._write_linear_matrix()

    def rotate_by(
        self,
        angle_degrees: float,
        axis: Vector3,
    ) -> None:
        delta = Quaternion.from_axis_angle(
            axis,
            angle_degrees,
        )

        self.set_rotation(
            (delta * self.rotation).normalize(),
        )

    # =================================== #
    # Matrix
    # =================================== #

    def write_matrix4(
        self,
        out: Matrix4,
        *,
        origin: Vector3 | None = None,
    ) -> None:
        """
        Writes this transform's local matrix into an existing Matrix4.

        No Matrix4 allocation.
        No NumPy array allocation.

        If origin is provided, applies pivot/origin behavior:

            translation = translation + origin - linear @ origin
        """

        out.set_from(
            self.matrix,
        )

        if origin is None:
            return

        values = out.values

        ox = origin.x
        oy = origin.y
        oz = origin.z

        lx = (
            values[0, 0] * ox
            + values[0, 1] * oy
            + values[0, 2] * oz
        )
        ly = (
            values[1, 0] * ox
            + values[1, 1] * oy
            + values[1, 2] * oz
        )
        lz = (
            values[2, 0] * ox
            + values[2, 1] * oy
            + values[2, 2] * oz
        )

        values[0, 3] += ox - lx
        values[1, 3] += oy - ly
        values[2, 3] += oz - lz

    def to_matrix4(
        self,
        origin: Vector3 | None = None,
    ) -> Matrix4:
        """
        Compatibility API.

        This still allocates because it returns a new Matrix4.
        Do not use this inside renderer hot paths.
        """

        matrix = Matrix4.empty()

        self.write_matrix4(
            matrix,
            origin=origin,
        )

        return matrix

    # =================================== #
    # Internal Matrix Writers
    # =================================== #

    def _write_full_matrix(
        self,
    ) -> None:
        self._write_linear_matrix()

        values = self.matrix.values
        values[0, 3] = self.translation.x
        values[1, 3] = self.translation.y
        values[2, 3] = self.translation.z

        values[3, 0] = 0.0
        values[3, 1] = 0.0
        values[3, 2] = 0.0
        values[3, 3] = 1.0

    def _write_linear_matrix(
        self,
    ) -> None:
        """
        Writes rotation @ scale directly into matrix[:3, :3].

        This replaces:

            rotation_matrix = rotation.to_matrix3()
            scale_matrix = np.diag(...)
            linear = rotation_matrix.values @ scale_matrix

        with direct scalar math and no allocations.
        """

        values = self.matrix.values

        sx = self.scale.x
        sy = self.scale.y
        sz = self.scale.z

        x = self.rotation.x
        y = self.rotation.y
        z = self.rotation.z
        w = self.rotation.w

        xx = x * x
        yy = y * y
        zz = z * z

        xy = x * y
        xz = x * z
        yz = y * z

        wx = w * x
        wy = w * y
        wz = w * z

        # rotation @ scale
        # Scale affects columns.
        values[0, 0] = (1.0 - 2.0 * (yy + zz)) * sx
        values[0, 1] = (2.0 * (xy - wz)) * sy
        values[0, 2] = (2.0 * (xz + wy)) * sz

        values[1, 0] = (2.0 * (xy + wz)) * sx
        values[1, 1] = (1.0 - 2.0 * (xx + zz)) * sy
        values[1, 2] = (2.0 * (yz - wx)) * sz

        values[2, 0] = (2.0 * (xz - wy)) * sx
        values[2, 1] = (2.0 * (yz + wx)) * sy
        values[2, 2] = (1.0 - 2.0 * (xx + yy)) * sz

        # Preserve translation.
        values[3, 0] = 0.0
        values[3, 1] = 0.0
        values[3, 2] = 0.0
        values[3, 3] = 1.0






