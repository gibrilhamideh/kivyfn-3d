# kivyfn/three/helpers/grid.py

from __future__ import annotations

from kivyfn.three.objects.material import Material
from kivyfn.three.objects.object3d import Object3D
from kivyfn.three.objects.geometry import Geometry


class GridHelper(Object3D):
    def __init__(
        self,
        material: Material,
        size: float = 10.0,
        divisions: int = 10,
        axis: str = "xz",
        **kwargs,
    ):
        divisions = max(1, divisions)

        geometry = self._create_geometry(
            size=size,
            divisions=divisions,
            axis=axis,
        )


        super().__init__(
            geometry=geometry,
            material=material,
            **kwargs,
        )

    def _create_geometry(
        self,
        size: float,
        divisions: int,
        axis: str,
    ) -> Geometry:
        half = size / 2.0
        step = size / divisions

        vertices: list[float] = []
        indices: list[int] = []

        def add_vertex(x: float, y: float, z: float) -> int:
            index = len(vertices) // 8
            vertices.extend([
                x, y, z,
                0.0, 1.0, 0.0,
                0.0, 0.0,
            ])
            return index

        def add_line(a, b) -> None:
            i0 = add_vertex(*a)
            i1 = add_vertex(*b)
            indices.extend([i0, i1])

        for i in range(divisions + 1):
            offset = -half + (i * step)

            if axis == "xz":
                add_line((offset, 0.0, -half), (offset, 0.0, half))
                add_line((-half, 0.0, offset), (half, 0.0, offset))

            elif axis == "xy":
                add_line((offset, -half, 0.0), (offset, half, 0.0))
                add_line((-half, offset, 0.0), (half, offset, 0.0))

            elif axis == "yz":
                add_line((0.0, offset, -half), (0.0, offset, half))
                add_line((0.0, -half, offset), (0.0, half, offset))

            else:
                raise ValueError("axis must be 'xy', 'xz', or 'yz'")

        return Geometry(
            name="GridHelper",
            vertices=vertices,
            indices=indices,
            mode="lines"
        )
