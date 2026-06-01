# kivyfn/three/scene/object3d.py

from __future__ import annotations

from typing import Literal, NoReturn, TYPE_CHECKING

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


Pivot = Literal[
    "center",
    "bottom",
    "top",
    "left",
    "right"
]


class Object3D(Node3D):

    render_id : int | None = NumericProperty(None)
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

    __events__ = ("on_material_dirty", )

    def __init__(
        self,
        geometry: Geometry,
        material: Material,
        name: str = "",
        pivot: Pivot = "center",
        uid: str | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            uid=uid,
            **kwargs,
        )

        self.geometry = geometry
        self.pivot = pivot
        self.collider = Collider(self)

        self.bind_collider()
        self.set_material(material)

    # =================================== #
    # Property Helpers
    # =================================== #
    @property
    def is_object(self) -> bool:
        return True

    # =================================== #
    # Requirements
    # =================================== #
    def require_render_id(self) -> int | NoReturn:
        if self.render_id is None:
            raise ValueError(
                f"Object3D '{self.name}' has no render_id assigned. "
                "Add the object to a Scene before accessing render_id."
            )

        return self.render_id 

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
    # Material
    # =================================== #
    def set_material(
        self,
        material: Material,
    ) -> None:
        if self.material is not None:
            self.unbind_material(self.material)

        self.material = material

        self.bind_material(material)
        self.mark_material_dirty()

    def bind_material(
        self,
        material: Material,
    ) -> None:
        material.bind(
            uniforms=self._on_material_changed,
            base_texture=self._on_material_changed,
            normal_texture=self._on_material_changed,
            emissive_texture=self._on_material_changed,
            metallic_roughness_texture=self._on_material_changed,
            occlusion_texture=self._on_material_changed,
            roughness_texture=self._on_material_changed,
            metallic_texture=self._on_material_changed,
            specular_texture=self._on_material_changed,
            displacement_texture=self._on_material_changed,
        )

    def unbind_material(
        self,
        material: Material,
    ) -> None:
        material.unbind(
            uniforms=self._on_material_changed,
            base_texture=self._on_material_changed,
            normal_texture=self._on_material_changed,
            emissive_texture=self._on_material_changed,
            metallic_roughness_texture=self._on_material_changed,
            occlusion_texture=self._on_material_changed,
            roughness_texture=self._on_material_changed,
            metallic_texture=self._on_material_changed,
            specular_texture=self._on_material_changed,
            displacement_texture=self._on_material_changed,
        )

    def _on_material_changed(self, *_):
        self.mark_material_dirty()

    # =================================== #
    # Dirty Propagation
    # =================================== #
    def mark_material_dirty(self) -> None:
        self.dispatch("on_material_dirty")

    # =================================== #
    # Events
    # =================================== #
    def on_material_dirty(
        self,
    ) -> None:
        pass





