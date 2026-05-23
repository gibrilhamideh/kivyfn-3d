# kivyfn/three/helpers/axis.py

from __future__ import annotations

from kivyfn.three.scene.node import Node3D
from kivyfn.three.objects import Material, Geometry, Object3D


class _AxisLine(Object3D):
    def __init__(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        material: Material,
        **kwargs,
    ):
        vertices = [
            # start
            start[0], start[1], start[2],
            0.0, 1.0, 0.0,
            0.0, 0.0,

            # end
            end[0], end[1], end[2],
            0.0, 1.0, 0.0,
            1.0, 0.0,
        ]

        indices = [0, 1]

        geometry = Geometry(
            vertices=vertices,
            indices=indices,
            mode="lines"
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

        # X axis (Red)
        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(size, 0.0, 0.0),
                material=Material(
                    name="XAxis",
                    uniforms={"object_color": [1.0, 0.0, 0.0, 1.0]}
                ),
            )
        )

        # Y axis (Green)
        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, size, 0.0),
                material=Material(
                    name="YAxis",
                    uniforms={"object_color": [0.0, 1.0, 0.0, 1.0]}
                ),
            )
        )

        # Z axis (Blue)
        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, 0.0, size),
                material=Material(
                    name="ZAxis",
                    uniforms={"object_color": [0.0, 0.0, 1.0, 1.0]}
                ),
            )
        )

