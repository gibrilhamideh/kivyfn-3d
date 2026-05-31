# kivyfn/three/scene/controller.py
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, overload


if TYPE_CHECKING:
    from kivyfn.three.objects.object3d import Object3D
    from kivyfn.three.scene.node import Node3D
    from kivyfn.three.scene.timeline.timeline import Timeline


NodeFilter = Literal[
    "all",
    "nodes",
    "objects",
]

SceneNode: TypeAlias = "Node3D | Object3D"
TimelineRef: TypeAlias = "Timeline | str"


class Controller:
    def __init__(
        self,
        node: SceneNode,
    ) -> None:
        self.node = node

        self.timelines: list[Timeline] = []
        self.timelines_map: dict[str, Timeline] = {}

    # =================================== #
    # Timelines
    # =================================== #

    def add_timeline(
        self,
        timeline: Timeline,
        *,
        name: str | None = None,
        replace: bool = False,
    ) -> Timeline:
        timeline_name = name if name is not None else timeline.name

        if timeline in self.timelines:
            return timeline

        if timeline_name:
            if not replace and timeline_name in self.timelines_map:
                raise ValueError(
                    f"Timeline name already exists: {timeline_name!r}"
                )

            timeline.name = timeline_name
            self.timelines_map[timeline_name] = timeline

        self.timelines.append(timeline)

        return timeline

    def remove_timeline(
        self,
        timeline: TimelineRef,
        *,
        stop: bool = True,
    ) -> Timeline | None:
        resolved = self._resolve_timeline(timeline)

        if resolved is None:
            return None

        if stop:
            resolved.stop()

        if resolved in self.timelines:
            self.timelines.remove(resolved)

        for name, mapped in list(self.timelines_map.items()):
            if mapped is resolved:
                del self.timelines_map[name]

        return resolved

    def start_timeline(
        self,
        timeline: TimelineRef | None = None,
        *,
        restart: bool = True,
    ) -> None:
        if timeline is None:
            for item in self.timelines:
                item.start(restart=restart)

            return

        resolved = self._resolve_timeline(timeline)

        if resolved is None:
            raise ValueError(f"Timeline not found: {timeline!r}")

        resolved.start(restart=restart)

    def stop_timeline(
        self,
        timeline: TimelineRef | None = None,
    ) -> None:
        if timeline is None:
            for item in self.timelines:
                item.stop()

            return

        resolved = self._resolve_timeline(timeline)

        if resolved is None:
            raise ValueError(f"Timeline not found: {timeline!r}")

        resolved.stop()

    def _resolve_timeline(
        self,
        timeline: TimelineRef,
    ) -> Timeline | None:
        if isinstance(timeline, str):
            return self.timelines_map.get(timeline)

        if timeline in self.timelines:
            return timeline

        return None

    # =================================== #
    # Traversal
    # =================================== #

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
    ) -> Iterator[SceneNode]:
        ...

    def walk(
        self,
        *,
        filter: NodeFilter = "all",
        include_self: bool = True,
    ) -> Iterator[Any]:
        for node in self.node.walk_tree():
            if not include_self and node is self.node:
                continue

            if self._matches_filter(
                node=node,
                filter=filter,
            ):
                yield node

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
    ) -> list[SceneNode]:
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

    # =================================== #
    # Parent / Ancestors
    # =================================== #

    @overload
    def parent(
        self,
        *,
        filter: Literal["nodes"],
    ) -> Node3D | None:
        ...

    @overload
    def parent(
        self,
        *,
        filter: Literal["objects"],
    ) -> Object3D | None:
        ...

    @overload
    def parent(
        self,
        *,
        filter: Literal["all"] = "all",
    ) -> SceneNode | None:
        ...

    def parent(
        self,
        *,
        filter: NodeFilter = "all",
    ) -> Any | None:
        parent = self.node.parent

        if parent is None:
            return None

        if self._matches_filter(
            node=parent,
            filter=filter,
        ):
            return parent

        return None

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
    ) -> list[SceneNode]:
        ...

    def ancestors(
        self,
        *,
        filter: NodeFilter = "all",
    ) -> list[Any]:
        result: list[Any] = []
        current = self.node.parent

        while current is not None:
            if self._matches_filter(
                node=current,
                filter=filter,
            ):
                result.append(current)

            current = current.parent

        return result

    # =================================== #
    # Find
    # =================================== #

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
    ) -> SceneNode | None:
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
    ) -> list[SceneNode]:
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
    ) -> list[SceneNode]:
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
        result: list[Any] = []

        for node in self.walk(
            filter=filter,
            include_self=include_self,
        ):
            name = node.name if case_sensitive else node.name.lower()

            if needle in name:
                result.append(node)

        return result

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

    # =================================== #
    # Visibility
    # =================================== #

    def show(self) -> None:
        self.node.visible = True

    def hide(self) -> None:
        self.node.visible = False

    def show_all(self) -> None:
        for node in self.walk():
            node.visible = True

    def hide_all(self) -> None:
        for node in self.walk():
            node.visible = False

    # =================================== #
    # Internal
    # =================================== #

    def _matches_filter(
        self,
        *,
        node: SceneNode,
        filter: NodeFilter,
    ) -> bool:
        if filter == "all":
            return True

        if filter == "objects":
            return node.is_object

        return not node.is_object
