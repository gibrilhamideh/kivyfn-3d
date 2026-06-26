# kivyfn/three/assets/object3d.py

from __future__ import annotations

from typing import NoReturn, TYPE_CHECKING

from kivy.properties import (
        NumericProperty,
        ObjectProperty,
        BooleanProperty
)

from kivyfn.three.collision import Collider
from kivyfn.three.graph.node import Node3D

if TYPE_CHECKING:
    from kivyfn.three.assets.geometry import Geometry
    from kivyfn.three.assets.material import Material


class Object3D(Node3D):

    render_id : int | None = NumericProperty(None)
    geometry: Geometry = ObjectProperty()
    material: Material = ObjectProperty()

    pickable: bool = BooleanProperty(False)
    grabable: bool = BooleanProperty(False)
    cast_shadow: bool = BooleanProperty(False)

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
            ")"
        )

    __events__ = ("on_material_dirty", "on_tag_dirty")

    def __init__(
        self,
        geometry: Geometry,
        material: Material,
        name: str = "",
        uid: str | None = None,
        *,
        tags: set[str] | None = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            uid=uid,
            **kwargs,
        )


        self._tags = set(tags or ())

        self.geometry = geometry
        self.collider = Collider(self)

        self.set_material(material)

    # =================================== #
    # Properties
    # =================================== #
    @property
    def kind(self):
        return "object"

    @property
    def tags(self) -> set[str]:
        return set(self._tags)

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
        material.bind(on_dirty=self._on_material_changed)


    def unbind_material(
        self,
        material: Material,
    ) -> None:

        material.unbind(on_dirty=self._on_material_changed)

    def _on_material_changed(self, *_):
        self.mark_material_dirty()

    # =================================== #
    # Dirty Propagation
    # =================================== #
    def mark_material_dirty(self) -> None:
        self.dispatch("on_material_dirty")

    def mark_tag_dirty(self, old: set[str]) -> None:
        new = self.tags
        self.dispatch("on_tag_dirty", old, new)

        if self.scene is not None:
            self.scene.renderer.queue_retag(self, old, new)

    # =================================== #
    # Tags
    # =================================== #
    def tag(self, tag: str) -> None:
        if tag in self.tags:
            return

        old = set(self.tags)
        self._tags.add(tag)
        self.mark_tag_dirty(old)

    def untag(self, tag: str) -> None:
        if tag not in self.tags:
            return

        old = set(self.tags)
        self._tags.remove(tag)
        self.mark_tag_dirty(old)


    def set_tags(self, tags: set[str]) -> None:
        tags = set(tags)

        if self.tags == tags:
            return

        old = set(self.tags)
        self._tags = tags
        self.mark_tag_dirty(old)

    # =================================== #
    # Events
    # =================================== #
    def on_material_dirty(
        self,
    ) -> None:
        pass

    def on_tag_dirty(self, old: set[str], new: set[str]) -> None:
        pass





