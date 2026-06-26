# kivyfn/three/scene/view.py

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Literal

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ObjectProperty, OptionProperty

from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.vector import Vector3
from kivyfn.three.types import CubeFaceName


ProjectionMode = Literal[
    "perspective",
    "orthographic",
]

ViewMode = Literal[
    "planar",
    "cube",
]


CUBE_FACE_VIEWS = MappingProxyType(
    {
        "px": (Vector3(1.0, 0.0, 0.0), Vector3(0.0, -1.0, 0.0)),
        "nx": (Vector3(-1.0, 0.0, 0.0), Vector3(0.0, -1.0, 0.0)),
        "py": (Vector3(0.0, 1.0, 0.0), Vector3(0.0, 0.0, 1.0)),
        "ny": (Vector3(0.0, -1.0, 0.0), Vector3(0.0, 0.0, -1.0)),
        "pz": (Vector3(0.0, 0.0, 1.0), Vector3(0.0, -1.0, 0.0)),
        "nz": (Vector3(0.0, 0.0, -1.0), Vector3(0.0, -1.0, 0.0)),
    }
)


class View(EventDispatcher):
    position: Vector3 = ObjectProperty(Vector3.zero())
    target: Vector3 = ObjectProperty(Vector3.zero())
    up: Vector3 = ObjectProperty(Vector3(0.0, 1.0, 0.0))

    near: float = NumericProperty(1.0)
    far: float = NumericProperty(1000.0)

    fov: float = NumericProperty(45.0)
    ortho_size: float = NumericProperty(20.0)

    projection: ProjectionMode = OptionProperty(
        "perspective",
        options=[
            "perspective",
            "orthographic",
        ],
    )

    __events__ = (
        "on_dirty",
    )

    def __repr__(self) -> str:
        return (
            "View(\n"
            f"  projection={self.projection!r},\n"
            f"  fov={self.fov:.1f},\n"
            f"  near={self.near:.3f},\n"
            f"  far={self.far:.3f},\n"
            f"  ortho_size={self.ortho_size:.3f},\n"
            f"  position={self.position},\n"
            f"  target={self.target},\n"
            f"  up={self.up}\n"
            ")"
        )

    def __init__(
        self,
        position: Vector3 | None = None,
        target: Vector3 | None = None,
        up: Vector3 | None = None,
        *,
        near: float = 1.0,
        far: float = 1000.0,
        fov: float = 45.0,
        ortho_size: float = 20.0,
        projection: ProjectionMode = "perspective",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.position = position or Vector3(0.0, 0.0, 10.0)
        self.target = target or Vector3.zero()
        self.up = up or Vector3(0.0, 1.0, 0.0)

        self.near = near
        self.far = far
        self.fov = fov
        self.ortho_size = ortho_size
        self.projection = projection

        self.bind(
            position=self._mark_dirty,
            target=self._mark_dirty,
            up=self._mark_dirty,
            near=self._mark_dirty,
            far=self._mark_dirty,
            fov=self._mark_dirty,
            ortho_size=self._mark_dirty,
            projection=self._mark_dirty,
        )

    def _mark_dirty(self, *_: Any) -> None:
        self.dispatch("on_dirty")

    def on_dirty(self) -> None:
        pass

    def get_camera_position(self) -> list[float]:
        position = self.position
        return [position.x, position.y, position.z]

    def tan_half_fov(self) -> float:
        return math.tan(math.radians(self.fov) / 2.0)

    def set_look_at(
        self,
        position: Vector3,
        target: Vector3,
        up: Vector3 | None = None,
    ) -> None:
        self.position = position
        self.target = target
        if up is not None:
            self.up = up

    # =================================== #
    # Unified Matrix API
    # =================================== #

    def get_view_matrix(
        self,
        *,
        mode: ViewMode = "planar",
        face: CubeFaceName | None = None,
    ) -> Matrix4:
        """
        Returns the look-at view matrix based on the mode.
        """
        if mode == "planar":
            if face is not None:
                raise ValueError("face_name cannot be used with mode='planar'")
            return Matrix4.look_at(self.position, self.target, self.up)

        if mode == "cube":
            if face is None:
                raise ValueError("face_name is required when mode='cube'")
            direction, up = CUBE_FACE_VIEWS[face]
            return Matrix4.look_at(self.position, self.position + direction, up)

        raise ValueError(f"Unknown view mode: {mode}")

    def get_projection_matrix(
        self,
        *,
        mode: ViewMode = "planar",
        aspect: float | None = None,
    ) -> Matrix4:
        """
        Returns the clip projection matrix based on the mode.
        """
        if mode == "planar":
            if aspect is None:
                raise ValueError("aspect is required when mode='planar'")
            return self._get_planar_projection(aspect)

        if mode == "cube":
            if aspect is not None:
                raise ValueError("aspect cannot be used with mode='cube'")
            return self._get_cube_projection()

        raise ValueError(f"Unknown view mode: {mode}")

    # =================================== #
    # Private Projection Math Helpers
    # =================================== #

    def _get_planar_projection(self, aspect: float) -> Matrix4:
        perspective = 1.0 if self.projection == "perspective" else 0.0
        if aspect <= 0.0:
            aspect = 1.0

        if self.projection == "orthographic":
            right = self.ortho_size / 2.0
            left = -right
            top = right / aspect
            bottom = -top
        else:
            top = self.near * self.tan_half_fov()
            bottom = -top
            right = top * aspect
            left = -right

        return Matrix4.view_clip(
            left, right, bottom, top, self.near, self.far, perspective
        )

    def _get_cube_projection(self) -> Matrix4:
        # Cube views always have a 90-degree FOV and a 1:1 aspect ratio
        top = self.near * math.tan(math.radians(90.0) / 2.0)
        bottom = -top
        right = top
        left = -right

        return Matrix4.view_clip(
            left, right, bottom, top, self.near, self.far, 1.0
        )


