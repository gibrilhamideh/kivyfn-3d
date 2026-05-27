# kivyfn/three/primitives/plane.py

from __future__ import annotations

import numpy as np

from kivy.properties import OptionProperty

from kivyfn.three.objects.material import Material
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.objects.geometry import Geometry


class Plane(Object3D):
    axis = OptionProperty(
        "xz",
        options=("xy", "xz", "yz"),
    )

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.0,
        axis: str = "xz",
        material: Material | None = None,
        **kwargs,
    ):
        self.axis = axis

        geometry = self._create_geometry(
            width=width,
            height=height,
            axis=axis,
        )

        super().__init__(
            geometry=geometry,
            material=material or Material(),
            **kwargs,
        )

    def _create_geometry(
        self,
        width: float,
        height: float,
        axis: str,
    ) -> Geometry:
        hw = width / 2.0
        hh = height / 2.0

        if axis == "xy":
            vertices = [
                -hw, -hh, 0.0,  0, 0, 1,  0, 0,  1, 0, 0, 1,
                 hw, -hh, 0.0,  0, 0, 1,  1, 0,  1, 0, 0, 1,
                 hw,  hh, 0.0,  0, 0, 1,  1, 1,  1, 0, 0, 1,
                -hw,  hh, 0.0,  0, 0, 1,  0, 1,  1, 0, 0, 1,
            ]

        elif axis == "xz":
            vertices = [
                -hw, 0.0, -hh,  0, 1, 0,  0, 0,  1, 0, 0, 1,
                 hw, 0.0, -hh,  0, 1, 0,  1, 0,  1, 0, 0, 1,
                 hw, 0.0,  hh,  0, 1, 0,  1, 1,  1, 0, 0, 1,
                -hw, 0.0,  hh,  0, 1, 0,  0, 1,  1, 0, 0, 1,
            ]

        elif axis == "yz":
            vertices = [
                0.0, -hw, -hh,  1, 0, 0,  0, 0,  0, 1, 0, 1,
                0.0,  hw, -hh,  1, 0, 0,  1, 0,  0, 1, 0, 1,
                0.0,  hw,  hh,  1, 0, 0,  1, 1,  0, 1, 0, 1,
                0.0, -hw,  hh,  1, 0, 0,  0, 1,  0, 1, 0, 1,
            ]

        else:
            raise ValueError(
                f"Invalid plane axis {axis!r}. "
                "Expected 'xy', 'xz', or 'yz'."
            )

        indices = [
            0, 1, 2,
            2, 3, 0,
        ]

        return Geometry(
            vertices=np.array(
                vertices,
                dtype=np.float32,
            ),
            indices=np.array(
                indices,
                dtype=np.uint16,
            ),
            has_source_tangents=False,
        )
