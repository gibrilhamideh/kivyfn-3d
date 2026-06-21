# kivyfn/three/graph/node.py

from __future__ import annotations
from collections.abc import Callable


from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Iterator,
    TypeGuard,
    TypeVar,
    overload,
)

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
    DictProperty,
)

from kivyfn.three.math.vector import Vector3
from kivyfn.three.math.transform import Transform

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.math.quaternion import Quaternion
    from kivyfn.three.math.matrix import Matrix4
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.controls.interaction import InteractionEvent
    from kivyfn.three.behaviors.behavior import Behavior


WalkFilter = Callable[["SceneObject"], bool]

NodeFilter = Literal[
    "all",
    "lights",
    "nodes",
    "objects",
]

NodeKind = Literal[
    "light",
    "node",
    "object",
]


B = TypeVar("B", bound="Behavior")


class Node3D(EventDispatcher):

    uid: str | None = StringProperty(None, allownone=True)
    name: str = StringProperty("")
    visible: bool = BooleanProperty(True)

    children: list[Node3D | Object3D | Light3D] = ListProperty([])
    parent: Node3D | Object3D | Light3D | None = ObjectProperty(
        None,
        allownone=True,
    )
    extras: dict = DictProperty()

    origin: Vector3 = ObjectProperty(Vector3.zero())
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
        uid: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.uid = uid
        self.name = name
        self.transform = transform or Transform()
        self.behaviors: dict[str, Behavior] = {}

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
        return self.transform.to_matrix4(origin=self.origin)

    @property
    def world_matrix(self) -> Matrix4:
        if self.parent is None:
            return self.local_matrix

        return self.parent.world_matrix @ self.local_matrix

    @property
    def world_position(self) -> Vector3:
        return self.world_matrix.transform_point(Vector3(0.0, 0.0, 0.0))

    @property
    def world_forward(self) -> Vector3:
        return self.world_matrix.transform_direction(
            Vector3(0.0, 0.0, -1.0)
        ).normalize()

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
    def on_transform_dirty(self) -> None:
        pass

    def on_visibility_dirty(self) -> None:
        pass

    # =================================== #
    # Relationships
    # =================================== #
    def add_child(
        self,
        child: Node3D | Object3D | Light3D,
    ) -> None:
        if child.parent is self:
            return

        if child.parent is not None:
            child.parent.remove_child(child)

        self.children.append(child)
        child.parent = self

        child.mark_transform_dirty()
        child.mark_visibility_dirty()

    def remove_child(
        self,
        child: Node3D | Object3D | Light3D,
    ) -> None:
        self.children.remove(child)
        child.parent = None

        child.mark_transform_dirty()
        child.mark_visibility_dirty()

    def clear_children(self) -> None:
        for child in list(self.children):
            self.remove_child(child)

    # =================================== #
    # Type Helpers
    # =================================== #
    @property
    def kind(self) -> NodeKind:
        return "node"

    @property
    def is_light(self) -> bool:
        return self.kind == "light"

    @property
    def is_object(self) -> bool:
        return self.kind == "object"

    def is_object3d(
        self,
        node: SceneObject,
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
    def __iter__(self) -> Iterator[Node3D | Object3D | Light3D]:
        return iter(self.children)

    def root(self) -> SceneObject:
        current: SceneObject = self

        while current.parent is not None:
            current = current.parent

        return current

    @overload
    def walk(
        self,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Node3D]:
        ...

    @overload
    def walk(
        self,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Object3D]:
        ...

    @overload
    def walk(
        self,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Light3D]:
        ...

    @overload
    def walk(
        self,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[SceneObject]:
        ...

    def walk(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Any]:
        if include_self and self._matches_walk(
            self,
            filter=filter,
            include=include,
            exclude=exclude,
        ):
            yield self

        for child in self.children:
            yield from child.walk(
                filter=filter,
                include_self=True,
                include=include,
                exclude=exclude,
            )

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["nodes"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Node3D]:
        ...

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["objects"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Object3D]:
        ...

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["lights"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Light3D]:
        ...

    @overload
    def walk_ancestors(
        self,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[SceneObject]:
        ...

    def walk_ancestors(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Iterator[Any]:
        current: SceneObject | None = self if include_self else self.parent

        while current is not None:
            if self._matches_walk(
                current,
                filter=filter,
                include=include,
                exclude=exclude,
            ):
                yield current

            current = current.parent

    def nodes(
        self,
        *,
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Node3D]:
        return list(
            self.walk(
                filter="nodes",
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
        )

    def objects(
        self,
        *,
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        return list(
            self.walk(
                filter="objects",
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
        )

    def lights(
        self,
        *,
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
        return list(
            self.walk(
                filter="lights",
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
        )

    @overload
    def descendants(
        self,
        *,
        filter: Literal["nodes"],
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Node3D]:
        ...

    @overload
    def descendants(
        self,
        *,
        filter: Literal["objects"],
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        ...

    @overload
    def descendants(
        self,
        *,
        filter: Literal["lights"],
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
        ...

    @overload
    def descendants(
        self,
        *,
        filter: Literal["all"] = "all",
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[SceneObject]:
        ...

    def descendants(
        self,
        *,
        filter: NodeFilter = "all",
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Any]:
        return list(
            self.walk(
                filter=filter,
                include_self=False,
                include=include,
                exclude=exclude,
            )
        )

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["nodes"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Node3D]:
        ...

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["objects"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        ...

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["lights"],
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
        ...

    @overload
    def ancestors(
        self,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[SceneObject]:
        ...

    def ancestors(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Any]:
        return list(
            self.walk_ancestors(
                filter=filter,
                include_self=include_self,
                include=include,
                exclude=exclude,
            )
        )

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["nodes"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Node3D | None:
        ...

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Object3D | None:
        ...

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Light3D | None:
        ...

    @overload
    def find(
        self,
        name: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> SceneObject | None:
        ...

    def find(
        self,
        name: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Any | None:
        for node in self.walk(
            filter=filter,
            include_self=include_self,
            include=include,
            exclude=exclude,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Node3D]:
        ...

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["objects"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        ...

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
        ...

    @overload
    def find_all(
        self,
        name: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[SceneObject]:
        ...

    def find_all(
        self,
        name: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Any]:
        return [
            node
            for node in self.walk(
                filter=filter,
                include_self=include_self,
                include=include,
                exclude=exclude,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Object3D | None:
        ...

    @overload
    def fuzzy_find(
        self,
        text: str,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Light3D | None:
        ...

    @overload
    def fuzzy_find(
        self,
        text: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> SceneObject | None:
        ...

    def fuzzy_find(
        self,
        text: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> Any | None:
        matches = self.fuzzy_find_all(
            text,
            filter=filter,
            include_self=include_self,
            case_sensitive=case_sensitive,
            include=include,
            exclude=exclude,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        ...

    @overload
    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
        ...

    @overload
    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: Literal["all"] = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[SceneObject]:
        ...

    def fuzzy_find_all(
        self,
        text: str,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        case_sensitive: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Any]:
        needle = text if case_sensitive else text.lower()

        return [
            node
            for node in self.walk(
                filter=filter,
                include_self=include_self,
                include=include,
                exclude=exclude,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Object3D]:
        ...

    @overload
    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: Literal["lights"],
        include_self: bool = True,
        require_value: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Light3D]:
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
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[SceneObject]:
        ...

    def find_by_extra(
        self,
        key: str,
        value: Any = None,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
        require_value: bool = False,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> list[Any]:
        result: list[Any] = []

        for node in self.walk(
            filter=filter,
            include_self=include_self,
            include=include,
            exclude=exclude,
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

    def on_visible(self, *_) -> None:
        self.mark_visibility_dirty()

    # =================================== #
    # Behaviors
    # =================================== #
    def add_behavior(
        self,
        behavior_type: type[B],
        *,
        name: str | None = None,
        **kwargs,
    ) -> B:
        behavior = behavior_type(
            self,
            name=name,
            **kwargs,
        )

        if behavior.name in self.behaviors:
            raise ValueError(
                f"Behavior {behavior.name!r} is already attached "
                f"to node {self.name!r}."
            )

        self.behaviors[behavior.name] = behavior
        return behavior

    def get_behavior(
        self,
        name: str,
    ) -> Behavior | None:
        return self.behaviors.get(name)

    def require_behavior(
        self,
        name: str,
    ) -> Behavior:
        behavior = self.get_behavior(name)

        if behavior is None:
            raise ValueError(
                f"Behavior not found on node {self.name!r}: {name!r}"
            )

        return behavior

    def remove_behavior(
        self,
        name: str,
    ) -> Behavior:
        behavior = self.behaviors.pop(name)

        behavior.destroy()
        return behavior

    # =================================== #
    # Internal
    # =================================== #
    def _matches_filter(
        self,
        node: SceneObject,
        filter: NodeFilter,
    ) -> bool:
        if filter == "all":
            return True

        if filter == "objects":
            return node.is_object

        if filter == "lights":
            return node.is_light

        if filter == "nodes":
            return node.kind == "node"

        return False

    def _matches_walk(
        self,
        node: SceneObject,
        *,
        filter: NodeFilter,
        include: WalkFilter | None = None,
        exclude: WalkFilter | None = None,
    ) -> bool:
        if not self._matches_filter(node, filter):
            return False

        if include is not None and not include(node):
            return False

        if exclude is not None and exclude(node):
            return False

        return True
