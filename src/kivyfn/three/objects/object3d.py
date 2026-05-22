# kivyfn/three/scene/object3d.py

from __future__ import annotations

from typing import Literal, TYPE_CHECKING

from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        OptionProperty,
)

from kivyfn.three.collision import Collider
from kivyfn.three.math.vector import Vector3
from kivyfn.three.objects.geometry import Geometry
from kivyfn.three.objects.material import Material
from kivyfn.three.scene.node import Node3D
from kivyfn.three.render.instructions import Instructions

if TYPE_CHECKING:
    from kivyfn.three.render.context import RenderContext


Pivot = Literal[
    "center",
    "bottom",
    "top",
    "left",
    "right"
]


# TODO: implmenets the following:
# print("watertight:", mesh.is_watertight)
# print("volume:", mesh.is_volume)
# print("winding:", mesh.is_winding_consistent)
# print("euler:", mesh.euler_number)

class Object3D(Node3D):
    ctx: RenderContext | None = ObjectProperty()
    geometry: Geometry = ObjectProperty()
    material: Material = ObjectProperty()
    instructions: Instructions | None = ObjectProperty()

    radius: float = NumericProperty(0.0)
    origin: Vector3 = ObjectProperty()
    bounds_min: Vector3 = ObjectProperty()
    bounds_max: Vector3 = ObjectProperty()

    pivot: Pivot = OptionProperty(
        "center",
        options=(
            "center",
            "bottom",
            "top",
            "left",
            "right"
        )
    )

    def __repr__(self) -> str:
        return (
            f"Object3D("
            f"name={self.name!r}, "
            f"geometry={self.geometry}, "
            f"children={len(self.children)})"
        )

    def __init__(
        self,
        geometry: Geometry,
        material: Material,
        name: str = "",
        pivot: Pivot = "center",
        **kwargs,
    ):
        super().__init__(
            name=name,
            **kwargs,
        )

        self.geometry = geometry
        self.material = material
        self.pivot = pivot
        self.collider = Collider(self)

        self.bind_collider()

    # =================================== #
    # Biners
    # =================================== #
    def bind_collider(self):

        # ---) binders
        self.bind(pivot=self.collider.setter("pivot"))

        self.collider.bind(origin=self.setter("origin"))
        self.collider.bind(radius=self.setter("radius"))
        self.collider.bind(bounds_min=self.setter("bounds_min"))
        self.collider.bind(bounds_max=self.setter("bounds_max"))

        # ---) sync
        self.collider.pivot = self.pivot
        self.collider.compute_bounds()

    # =================================== #
    # Rendering
    # =================================== #
    def attach(self, ctx):
        self.ctx = ctx
        self.instructions = Instructions(self, ctx)
        return True

    def detach(self):
        assert self.ctx is not None
        assert self.instructions is not None
        self.ctx.remove(self.instructions.group)

        self.ctx = None
        self.instructions = None
        return True

    # =================================== #
    # Collistions
    # =================================== #
    def intersects_ray(self, origin, direction):
        return self.collider.intersects_ray(origin, direction)

