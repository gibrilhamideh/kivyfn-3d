# kivyfn/three/helpers/axis.py

from __future__ import annotations

from kivyfn.three.render.material import Material
from kivyfn.three.render.meshdata import MeshData
from kivyfn.three.scene.node import Node3D
from kivyfn.three.scene.object3d import Object3D


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

        mesh_data = MeshData(
            vertices=vertices,
            indices=indices,
        )

        super().__init__(
            mesh_data=mesh_data,
            material=material,
            **kwargs,
        )

        self.render_mode = "lines"
        self.pickable = False


class AxisHelper(Node3D):
    def __init__(
        self,
        material: Material,
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
                    color=[1.0, 0.0, 0.0, 1.0],
                    shader=material.shader,
                ),
                name="XAxis",
            )
        )

        # Y axis (Green)
        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, size, 0.0),
                material=Material(
                    color=[0.0, 1.0, 0.0, 1.0],
                    shader=material.shader,
                ),
                name="YAxis",
            )
        )

        # Z axis (Blue)
        self.add_child(
            _AxisLine(
                start=(0.0, 0.0, 0.0),
                end=(0.0, 0.0, size),
                material=Material(
                    color=[0.0, 0.0, 1.0, 1.0],
                    shader=material.shader,
                ),
                name="ZAxis",
            )
        )

