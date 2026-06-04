# kivyfn/three/helpers/axis.py

from __future__ import annotations

import numpy as np

from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.material import Material
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.assets.geometry import Geometry


class _AxisLine(Object3D):
    def __init__(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        material: Material,
        **kwargs,
    ):
        vertices = np.array(
            [
                # start
                start[0], start[1], start[2],
                0.0, 1.0, 0.0,
                0.0, 0.0,

                # end
                end[0], end[1], end[2],
                0.0, 1.0, 0.0,
                1.0, 0.0,
            ],
            dtype=np.float32,
        )

        indices = np.array(
            [0, 1],
            dtype=np.uint16,
        )

        geometry = Geometry(
            vertices=vertices,
            indices=indices,
            mode="lines",
            fmt=[
                (b"v_pos", 3, "float"),
                (b"v_normal", 3, "float"),
                (b"v_uv", 2, "float"),
            ],
        )

        super().__init__(
            geometry=geometry,
            material=material,
            **kwargs,
        )

        self.pickable = False


class AxisHelper(Node3D):
    def __init__(
        self,
        size: float = 1.0,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(size, 0.0, 0.0),
                material=Material(
                    name="XAxis",
                    base_color=[1.0, 0.0, 0.0, 1.0],
                ),
            )
        )

        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, size, 0.0),
                material=Material(
                    name="YAxis",
                    base_color=[0.0, 1.0, 0.0, 1.0],
                ),
            )
        )

        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, 0.0, size),
                material=Material(
                    name="ZAxis",
                    base_color=[0.0, 0.0, 1.0, 1.0],
                ),
            )
        )
