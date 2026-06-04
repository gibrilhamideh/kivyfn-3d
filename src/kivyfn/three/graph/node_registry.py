# kivyfn/three/graph/node_registry.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.assets.object3d import Object3D


class SceneNodeRegistry:
    """
    Tracks scene nodes by uid and renderable objects by render_id.

    This class does not own the scene tree.
    It only indexes nodes that are already part of a Scene.
    """

    def __init__(self) -> None:
        self._next_render_id: int = 1

        self.by_uid: dict[str, Node3D] = {}
        self.by_render_id: dict[int, Object3D] = {}

    def __len__(self) -> int:
        return len(self.by_render_id)

    # =================================== #
    # Node API
    # =================================== #

    def register(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is not None:
            self.register_uid(node)

        if node.is_object3d(node):
            self.register_render_id(node)

    def unregister(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is not None:
            self.unregister_uid(node)

        if node.is_object3d(node):
            self.unregister_render_id(node)

    # =================================== #
    # UID API
    # =================================== #

    def register_uid(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is None:
            return

        if node.uid in self.by_uid:
            raise ValueError(f"Duplicate node uid: {node.uid!r}")

        self.by_uid[node.uid] = node

    def unregister_uid(
        self,
        node: Node3D,
    ) -> None:
        if node.uid is None:
            return

        self.by_uid.pop(node.uid, None)

    def get_by_uid(
        self,
        uid: str,
    ) -> Node3D | Object3D | None:
        return self.by_uid.get(uid)

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

        self.by_render_id[object3d.render_id] = object3d

    def unregister_render_id(
        self,
        object3d: Object3D,
    ) -> None:
        if object3d.render_id is None:
            return

        self.by_render_id.pop(object3d.render_id, None)

    def generate_render_id(self) -> int:
        render_id = self._next_render_id
        self._next_render_id += 1
        return render_id

    def get_by_render_id(
        self,
        render_id: int,
    ) -> Object3D | None:
        return self.by_render_id.get(render_id)

    # =================================== #
    # Clear
    # =================================== #

    def clear(self) -> None:
        self.by_uid.clear()
        self.by_render_id.clear()
        self._next_render_id = 1
