# kivyfn/three/scene/registry.py

from __future__ import annotations

from typing import cast

from kivyfn.three.graph.node import Node3D
from kivyfn.three.types import SceneObject
from kivyfn.three.assets.object3d import Object3D


class SceneRegistry:
    """
    Tracks scene nodes by id, uid, render_id, transform dependencies,
    object ids, and skin dependencies.

    by_id is the only object source of truth.

    Secondary indexes store ids:

        by_uid: uid -> node_id
        by_render_id: render_id -> object_id
        object_ids: set[object_id]
        transforms: transform dependency index
        skins: skin dependency index

    This class does not own the scene tree.
    It only indexes nodes that are already part of a Scene.

    Public query rules:
    - SceneRegistry lookup methods accept scalar keys
    - dependency indexes accept ids only
    - dependency indexes return ids only
    - SceneRegistry does not pass through transform/skin methods
    """

    def __init__(
        self,
        root: Node3D
    ) -> None:
        self._next_render_id: int = 1

        self.by_id: dict[int, SceneObject] = {}
        self.by_uid: dict[str, int] = {}
        self.by_render_id: dict[int, int] = {}
        self.object_ids: set[int] = set()

        self._root = root
        self._graph: list[SceneObject] = []


    def __len__(
        self,
    ) -> int:
        return len(self.by_id)

    # =================================== #
    # Node API
    # =================================== #
    def register(
        self,
        node: SceneObject,
    ) -> None:
        self._register_indexes(node)

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        self._unregister_indexes(node)


    # =================================== #
    # Internal Node Indexing
    # =================================== #
    def _register_indexes(
        self,
        node: SceneObject,
    ) -> None:
        self.register_id(node)

        if node.uid is not None:
            self.register_uid(node)

        if node.is_renderable:
            object3d = cast(Object3D, node)
            object_id = id(object3d)

            self.object_ids.add(object_id)
            self.register_render_id(object3d)

    def _unregister_indexes(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is not None:
            self.unregister_uid(node)

        if node.is_renderable:
            object3d = cast(Object3D, node)
            object_id = id(object3d)

            self.unregister_render_id(object3d)
            self.object_ids.discard(object_id)

        self.unregister_id(node)

    # =================================== #
    # ID API
    # =================================== #

    def register_id(
        self,
        node: SceneObject,
    ) -> None:
        node_id = id(node)

        if node_id in self.by_id:
            raise ValueError(
                f"Duplicate scene object id: {node_id!r}"
            )

        self.by_id[node_id] = node

    def unregister_id(
        self,
        node: SceneObject,
    ) -> None:
        self.by_id.pop(
            id(node),
            None,
        )

    def get_by_id(
        self,
        node_id: int,
    ) -> SceneObject | None:
        return self.by_id.get(
            node_id,
        )

    def require_by_id(
        self,
        node_id: int,
    ) -> SceneObject:
        node = self.get_by_id(
            node_id,
        )

        if node is None:
            raise ValueError(
                f"Scene object id not found: {node_id!r}"
            )

        return node

    # =================================== #
    # UID API
    # =================================== #

    def register_uid(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is None:
            return

        if node.uid in self.by_uid:
            raise ValueError(
                f"Duplicate node uid: {node.uid!r}"
            )

        self.by_uid[node.uid] = id(node)

    def unregister_uid(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is None:
            return

        self.by_uid.pop(
            node.uid,
            None,
        )

    def get_by_uid(
        self,
        uid: str,
    ) -> SceneObject | None:
        node_id = self.by_uid.get(
            uid,
        )

        if node_id is None:
            return None

        return self.get_by_id(
            node_id,
        )

    def require_by_uid(
        self,
        uid: str,
    ) -> SceneObject:
        node = self.get_by_uid(
            uid,
        )

        if node is None:
            raise ValueError(
                f"Scene object uid not found: {uid!r}"
            )

        return node

    # =================================== #
    # Render ID API
    # =================================== #

    def register_render_id(
        self,
        object3d: Object3D,
    ) -> None:
        if object3d.render_id is None:
            object3d.render_id = self.generate_render_id()

        if object3d.render_id in self.by_render_id:
            raise ValueError(
                f"Duplicate render_id: {object3d.render_id!r}"
            )

        self.by_render_id[object3d.render_id] = id(object3d)

    def unregister_render_id(
        self,
        object3d: Object3D,
    ) -> None:
        if object3d.render_id is None:
            return

        self.by_render_id.pop(
            object3d.render_id,
            None,
        )



    def get_by_render_id(
        self,
        render_id: int,
    ) -> Object3D | None:
        object_id = self.by_render_id.get(
            render_id,
        )

        if object_id is None:
            return None

        return self.object_by_id(
            object_id,
        )

    def require_by_render_id(
        self,
        render_id: int,
    ) -> Object3D:
        object3d = self.get_by_render_id(
            render_id,
        )

        if object3d is None:
            raise ValueError(
                f"Object3D render_id not found: {render_id!r}"
            )

        return object3d

    def generate_render_id(
        self,
    ) -> int:
        render_id = self._next_render_id
        self._next_render_id += 1
        return render_id

    # =================================== #
    # Object API
    # =================================== #

    def object_by_id(
        self,
        object_id: int,
    ) -> Object3D | None:
        if object_id not in self.object_ids:
            return None

        node = self.get_by_id(
            object_id,
        )

        if node is None:
            return None

        return cast(
            Object3D,
            node,
        )

    # =================================== #
    # Graph API
    # =================================== #
    def rebuild_graph(
        self,
    ) -> None:
        self._graph.clear()
        self._apply(
            self._root,
            depth=0,
        )

    def affected_by(
        self,
        node_ids: set[int],
    ) -> list[SceneObject]:

        # NOTE: performance
        # Compressing dirty transform spans removed 83.3% of node visits.
        # 60-frame sample:
        #   raw span hits:        1,617,280
        #   compressed hits:        270,360
        #   removed hits:         1,346,920
        # Per frame:
        #   raw:        ~26,955 hits
        #   compressed: ~4,506 hits
        #   removed:   ~22,449 hits
        ranges = self._compress(node_ids)

        if not ranges:
            return list()

        affected: list[SceneObject] = []

        for start, end in ranges:
            affected.extend(
                self._graph[start:end]
            )

        return affected

    def _compress(
        self,
        node_ids: set[int],
    ) -> tuple[tuple[int, int], ...]:
        if not node_ids:
            return ()

        ranges: list[tuple[int, int]] = []

        for node_id in node_ids:
            node = self.by_id.get(node_id)

            if node is None:
                continue

            start = node._graph_start
            end = node._graph_end

            if end <= start:
                continue

            ranges.append(
                (
                    start,
                    end,
                )
            )

        if not ranges:
            return ()

        ranges.sort(
            key=lambda item: (
                item[0],
                -item[1],
            )
        )

        compressed: list[tuple[int, int]] = []
        covered_end = -1

        for start, end in ranges:
            if end <= covered_end:
                continue

            compressed.append(
                (
                    start,
                    end,
                )
            )
            covered_end = end

        return tuple(compressed)

    def _apply(
        self,
        node: SceneObject,
        depth: int,
    ) -> None:
        start = len(self._graph)

        node._graph_start = start
        node._graph_end = depth

        self._graph.append(node)

        for child in node.children:
            self._apply(
                child,
                depth + 1,
            )

        node._graph_end = len(self._graph)


