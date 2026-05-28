# kivyfn/three/scene/object3d.py

from __future__ import annotations

from typing import Literal, TYPE_CHECKING

from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        OptionProperty,
        BooleanProperty
)

from kivyfn.three.collision import Collider
from kivyfn.three.scene.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.objects.geometry import Geometry
    from kivyfn.three.objects.material import Material
    from kivyfn.three.controls.interaction import InteractionEvent


Pivot = Literal[
    "center",
    "bottom",
    "top",
    "left",
    "right"
]


class Object3D(Node3D):
    geometry: Geometry = ObjectProperty()
    material: Material = ObjectProperty()

    pickable: bool = BooleanProperty(False)
    grabable: bool = BooleanProperty(False)

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

    __events__ = (
        "on_press",
        "on_release",
        "on_drag",
    )

    def __repr__(self) -> str:
        geometry_name = (
            self.geometry.name
            if self.geometry is not None
            else None
        )

        material_name = (
            self.material.name
            if self.material is not None
            else None
        )

        return (
            "Object3D("
            f"name={self.name!r}, "
            f"geometry={geometry_name!r}, "
            f"material={material_name!r}, "
            f"children={len(self.children)}, "
            f"pickable={self.pickable}, "
            f"grabable={self.grabable}"
            ")"
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
        self.material = material # type: ignore[reportIncompatibleVariableOverride]
        self.pivot = pivot
        self.collider = Collider(self)

        self.bind_collider()

    # =================================== #
    # Biners
    # =================================== #
    @property
    def is_object(self) -> bool:
        return True

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
    # Collistions
    # =================================== #
    def intersects_ray(self, origin, direction):
        return self.collider.intersects_ray(origin, direction)


    # =================================== #
    # Interaction Events
    # =================================== #
    def on_press(
        self,
        event: InteractionEvent,
    ) -> None:
        pass

    def on_release(
        self,
        event: InteractionEvent,
    ) -> None:
        pass

    def on_drag(
        self,
        event: InteractionEvent,
    ) -> None:
        pass
