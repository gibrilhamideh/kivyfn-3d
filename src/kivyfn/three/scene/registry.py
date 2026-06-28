# kivyfn/three/graph/node_registry.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D


class SkinDependencyRegistry:
    """
    Tracks reverse skin dependencies.

    Skin stores:

        Object3D -> Skin -> joints

    But dirty propagation needs the reverse direction:

        joint Node3D -> affected Object3D objects

    This registry does not own nodes, objects, or skins.
    It only indexes skinned Object3D instances that are already part
    of a Scene.
    """

    def __init__(self) -> None:
        self._by_joint: dict[Node3D, set[Object3D]] = {}

    def register(
        self,
        object3d: Object3D,
    ) -> None:
        skin = object3d.skin

        if skin is None:
            return

        for joint in skin.joints:
            self._by_joint.setdefault(
                joint,
                set(),
            ).add(object3d)

    def unregister(
        self,
        object3d: Object3D,
    ) -> None:
        skin = object3d.skin

        if skin is None:
            return

        for joint in skin.joints:
            objects = self._by_joint.get(joint)

            if objects is None:
                continue

            objects.discard(object3d)

            if not objects:
                del self._by_joint[joint]

    def affected_by(
        self,
        joint: Node3D,
    ) -> tuple[Object3D, ...]:
        return tuple(
            self._by_joint.get(
                joint,
                (),
            )
        )

    def clear(self) -> None:
        self._by_joint.clear()


class SceneRegistry:
    """
    Tracks scene nodes by uid, renderable objects by render_id,
    and skin dependencies by joint node.

    This class does not own the scene tree.
    It only indexes nodes that are already part of a Scene.
    """

    def __init__(self) -> None:
        self._next_render_id: int = 1

        self.by_uid: dict[str, SceneObject] = {}
        self.by_render_id: dict[int, Object3D] = {}

        self.skins = SkinDependencyRegistry()

    def __len__(self) -> int:
        return len(self.by_render_id)

    # =================================== #
    # Node API
    # =================================== #

    def register(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is not None:
            self.register_uid(node)

        if node.is_object3d(node):
            self.register_render_id(node)
            self.skins.register(node)

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is not None:
            self.unregister_uid(node)

        if node.is_object3d(node):
            self.skins.unregister(node)
            self.unregister_render_id(node)

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
            raise ValueError(f"Duplicate node uid: {node.uid!r}")

        self.by_uid[node.uid] = node

    def unregister_uid(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is None:
            return

        self.by_uid.pop(node.uid, None)

    def get_by_uid(
        self,
        uid: str,
    ) -> SceneObject | None:
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
    # Skin Dependency API
    # =================================== #

    def affected_by_joint(
        self,
        joint: Node3D,
    ) -> tuple[Object3D, ...]:
        return self.skins.affected_by(joint)

    # =================================== #
    # Clear
    # =================================== #

    def clear(self) -> None:
        self.by_uid.clear()
        self.by_render_id.clear()
        self.skins.clear()
        self._next_render_id = 1
