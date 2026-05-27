# kivyfn/three/scene/node.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, TypeGuard

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)

from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.math.quaternion import Quaternion
    from kivyfn.three.math.matrix import Matrix4
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.objects import Object3D
    from kivyfn.three.objects.material import Material


class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)

    children: list[Node3D | Object3D] = ListProperty([])
    parent: Node3D | Object3D | None = ObjectProperty(None, allownone=True)

    material: Material | None = ObjectProperty(None, allownone=True)

    transform: Transform = ObjectProperty()

    __events__ = (
        "on_transform_dirty",
        "on_material_dirty",
    )

    def __init__(
        self,
        name: str = "",
        transform: Transform | None = None,
        material: Material | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.set_material(material)
        self.name = name
        self.transform = transform or Transform()

    def __repr__(self) -> str:
        return (
            "Node3D("
            f"name={self.name!r}, "
            f"children={len(self.children)}, "
            f"visible={self.visible}"
            ")"
        )

    # =================================== #
    # Matrices
    # =================================== #
    @property
    def local_matrix(self) -> Matrix4:
        return self.transform.to_matrix4()

    @property
    def world_matrix(self) -> Matrix4:
        if self.parent is None:
            return self.local_matrix

        return self.parent.world_matrix @ self.local_matrix

    # =================================== #
    # Transform State
    # =================================== #
    @property
    def translation(self) -> Vector3:
        return self.transform.translation

    @property
    def rotation(self) -> Quaternion:
        return self.transform.rotation

    @property
    def scale(self) -> Vector3:
        return self.transform.scale

    # =================================== #
    # Translation
    # =================================== #
    def set_translation(
        self,
        translation: Vector3,
    ) -> None:
        self.transform.set_translation(translation)
        self.mark_transform_dirty()

    def translate_by(
        self,
        offset: Vector3,
    ) -> None:
        self.transform.translate_by(offset)
        self.mark_transform_dirty()

    # =================================== #
    # Scale
    # =================================== #
    def set_scale(
        self,
        scale: Vector3,
    ) -> None:
        self.transform.set_scale(scale)
        self.mark_transform_dirty()

    def scale_by(
        self,
        factor: Vector3,
    ) -> None:
        self.transform.scale_by(factor)
        self.mark_transform_dirty()

    # =================================== #
    # Rotation
    # =================================== #
    def set_rotation(
        self,
        rotation: Quaternion,
    ) -> None:
        self.transform.set_rotation(rotation)
        self.mark_transform_dirty()

    def rotate_by(
        self,
        angle_degrees: float,
        axis: Vector3,
    ) -> None:
        self.transform.rotate_by(
            angle_degrees,
            axis,
        )
        self.mark_transform_dirty()

    # =================================== #
    # Material
    # =================================== #
    def set_material(
        self,
        material: Material | None,
    ) -> None:
        if self.material is not None:
            self.unbind_material(self.material)

        self.material = material

        if material is not None:
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
    def mark_transform_dirty(self) -> None:
        self.dispatch("on_transform_dirty", self)

        for child in self.children:
            child.mark_transform_dirty()

    def mark_material_dirty(self) -> None:
        self.dispatch("on_material_dirty", self)

        for child in self.children:
            child.mark_material_dirty()

    # =================================== #
    # Events
    # =================================== #
    def on_transform_dirty(
        self,
        node: Node3D,
    ) -> None:
        pass

    def on_material_dirty(
        self,
        node: Node3D,
    ) -> None:
        pass

    # =================================== #
    # Relationships
    # =================================== #
    def add_child(
        self,
        child: Node3D | Object3D,
    ) -> None:
        if child.parent is self:
            return

        if child.parent is not None:
            child.parent.remove_child(child)

        self.children.append(child)
        child.parent = self

        child.mark_transform_dirty()
        child.mark_material_dirty()

    def remove_child(
        self,
        child: Node3D | Object3D,
    ) -> None:
        self.children.remove(child)
        child.parent = None

        child.mark_transform_dirty()
        child.mark_material_dirty()

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)

    # =================================== #
    # Traversal
    # =================================== #
    def __iter__(self) -> Iterator[Node3D | Object3D]:
        return iter(self.children)

    def walk_tree(self) -> Iterator[Node3D | Object3D]:
        yield self

        for child in self.children:
            yield from child.walk_tree()

    def walk_objects(self) -> Iterator[Object3D]:
        for node in self.walk_tree():
            if self.is_object3d(node):
                yield node

    # =================================== #
    # Type Helpers
    # =================================== #
    @property
    def is_object(self) -> bool:
        return False

    def is_object3d(
        self,
        node,
    ) -> TypeGuard[Object3D]:
        return node.is_object
