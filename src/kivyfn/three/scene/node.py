# kivyfn/three/scene/node.py

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Iterator,
    TypeGuard,
    TypeAlias,
    overload
)

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
    DictProperty
)

from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.math.quaternion import Quaternion
    from kivyfn.three.math.matrix import Matrix4
    from kivyfn.three.math.vector import Vector3
    from kivyfn.three.objects import Object3D
    from kivyfn.three.controls.interaction import InteractionEvent

NodeFilter = Literal[
    "all",
    "nodes",
    "objects",
]

SceneNode: TypeAlias = "Node3D | Object3D"

class Node3D(EventDispatcher):
    name = StringProperty("")
    visible = BooleanProperty(True)

    children: list[Node3D | Object3D] = ListProperty([])
    parent: Node3D | Object3D | None = ObjectProperty(None, allownone=True)
    extras: dict = DictProperty()


    transform: Transform = ObjectProperty()

    __events__ = (
        "on_transform_dirty",
        "on_visibility_dirty",
        "on_press",
        "on_release",
        "on_drag",
    )

    def __init__(
        self,
        name: str = "",
        transform: Transform | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

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
    # Dirty Propagation
    # =================================== #
    def mark_transform_dirty(self) -> None:
        self.dispatch("on_transform_dirty")

        for child in self.children:
            child.mark_transform_dirty()

    def mark_visibility_dirty(self) -> None:
        self.dispatch("on_visibility_dirty")

        for child in self.children:
            child.mark_visibility_dirty()

    # =================================== #
    # Events
    # =================================== #
    def on_transform_dirty(
        self,
    ) -> None:
        pass

    def on_visibility_dirty(
        self,
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

    def remove_child(
        self,
        child: Node3D | Object3D,
    ) -> None:
        self.children.remove(child)
        child.parent = None

        child.mark_transform_dirty()

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)



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


    # =================================== #
    # Traversal
    # =================================== #
    def __iter__(self) -> Iterator[Node3D | Object3D]:
        return iter(self.children)

    @overload
    def walk(
        self,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
    ) -> Iterator[Node3D]:
        ...

    @overload
    def walk(
        self,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
    ) -> Iterator[Object3D]:
        ...

    @overload
    def walk(
        self,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
    ) -> Iterator[Node3D | Object3D]:
        ...

    def walk(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
    ) -> Iterator[Any]:
        if include_self and self._matches_filter(self, filter):
            yield self

        for child in self.children:
            yield from child.walk(
                filter=filter,
                include_self=True,
            )

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["nodes"],
        include_self: bool = False,
    ) -> Iterator[Node3D]:
        ...

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["objects"],
        include_self: bool = False,
    ) -> Iterator[Object3D]:
        ...

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = False,
    ) -> Iterator[SceneNode]:
        ...

    def walk_ancestors(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = False,
    ) -> Iterator[Any]:
        current: SceneNode | None = (
            self if include_self else self.parent
        )

        while current is not None:
            if self._matches_filter(
                current,
                filter,
            ):
                yield current

            current = current.parent

    def nodes(
        self,
        *,
        include_self: bool = True,
    ) -> list[Node3D]:
        return list(
            self.walk(
                filter="nodes",
                include_self=include_self,
            )
        )

    def objects(
        self,
        *,
        include_self: bool = True,
    ) -> list[Object3D]:
        return list(
            self.walk(
                filter="objects",
                include_self=include_self,
            )
        )

    @overload
    def descendants(
        self,
        *,
        filter: Literal["nodes"],
    ) -> list[Node3D]:
        ...

    @overload
    def descendants(
        self,
        *,
        filter: Literal["objects"],
    ) -> list[Object3D]:
        ...

    @overload
    def descendants(
        self,
        *,
        filter: Literal["all"] = "all",
    ) -> list[Node3D | Object3D]:
        ...

    def descendants(
        self,
        *,
        filter: NodeFilter = "all",
    ) -> list[Any]:
        return list(
            self.walk(
                filter=filter,
                include_self=False,
            )
        )

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["nodes"],
    ) -> list[Node3D]:
        ...

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["objects"],
    ) -> list[Object3D]:
        ...

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["all"] = "all",
    ) -> list[Node3D | Object3D]:
        ...

    def ancestors(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = False,
    ) -> list[Any]:
        return list(
            self.walk_ancestors(
                filter=filter,
                include_self=include_self,
            )
        )

    def root(self) -> Node3D | Object3D:
        current: Node3D | Object3D = self

        while current.parent is not None:
            current = current.parent

        return current

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
    ) -> Node3D | None:
        ...

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
    ) -> Object3D | None:
        ...

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
    ) -> Node3D | Object3D | None:
        ...

    def find(
        self,
        name: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
    ) -> Any | None:
        for node in self.walk(
            filter=filter,
            include_self=include_self,
        ):
            if node.name == name:
                return node

        return None

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
    ) -> list[Node3D]:
        ...

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
    ) -> list[Object3D]:
        ...

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
    ) -> list[Node3D | Object3D]:
        ...

    def find_all(
        self,
        name: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
    ) -> list[Any]:
        return [
            node
            for node in self.walk(
                filter=filter,
                include_self=include_self,
            )
            if node.name == name
        ]

    @overload
    def fuzzy_find(
        self,
        text: str,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> Node3D | None:
        ...

    @overload
    def fuzzy_find(
        self,
        text: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> Object3D | None:
        ...

    @overload
    def fuzzy_find(
        self,
        text: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> SceneNode | None:
        ...

    def fuzzy_find(
        self,
        text: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> Any | None:
        matches = self.fuzzy_find_all(
            text,
            filter=filter,
            include_self=include_self,
            case_sensitive=case_sensitive,
        )

        return matches[0] if matches else None

    @overload
    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> list[Node3D]:
        ...

    @overload
    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> list[Object3D]:
        ...

    @overload
    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> list[Node3D | Object3D]:
        ...

    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
    ) -> list[Any]:
        needle = text if case_sensitive else text.lower()

        return [
            node
            for node in self.walk(
                filter=filter,
                include_self=include_self,
            )
            if needle in (
                node.name if case_sensitive else node.name.lower()
            )
        ]

    @overload
    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
        require_value: bool = False,
    ) -> list[Node3D]:
        ...

    @overload
    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        require_value: bool = False,
    ) -> list[Object3D]:
        ...

    @overload
    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        require_value: bool = False,
    ) -> list[SceneNode]:
        ...

    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        require_value: bool = False,
    ) -> list[Any]:
        result: list[Any] = []

        for node in self.walk(
            filter=filter,
            include_self=include_self,
        ):
            extras = getattr(node, "extras", None)

            if not isinstance(extras, dict):
                continue

            if key not in extras:
                continue

            if require_value and extras.get(key) != value:
                continue

            result.append(node)

        return result

    def require(
        self,
        name: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
    ) -> Any:
        node = self.find(
            name,
            filter=filter,
            include_self=include_self,
        )

        if node is None:
            raise ValueError(f"Node not found: {name!r}")

        return node

    # =================================== #
    # Visibility
    # =================================== #
    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    @property
    def visible_in_tree(self) -> bool:
        if not self.visible:
            return False

        if self.parent is None:
            return True

        return self.parent.visible_in_tree

    def on_visible(self, *_):
        self.mark_visibility_dirty()

    # =================================== #
    # Internal
    # =================================== #
    def _matches_filter(
        self,
        node: Node3D | Object3D,
        filter: NodeFilter,
    ) -> bool:
        if filter == "all":
            return True

        if filter == "objects":
            return node.is_object

        return not node.is_object
