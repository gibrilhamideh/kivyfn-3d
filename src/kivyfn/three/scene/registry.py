# kivyfn/three/graph/node_registry.py

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload, cast

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.graph.node import Node3D


class TreeDependencyRegistry:
    """
    Tracks transform-tree dependencies by object id.

    ancestor_id -> affected SceneObject ids

    If an ancestor SceneObject changes transform, every affected
    SceneObject has a changed world matrix.

    This registry does not own nodes.
    It only stores ids.
    """

    def __init__(self) -> None:
        self._by_ancestor: dict[int, set[int]] = {}
        self._depth_by_id: dict[int, int] = {}

    def register(
        self,
        node: SceneObject,
    ) -> None:
        node_id = id(node)

        depth = 0
        current: SceneObject | None = node.parent

        while current is not None:
            depth += 1
            current = current.parent

        self._depth_by_id[node_id] = depth

        current = node

        while current is not None:
            ancestor_id = id(current)

            self._by_ancestor.setdefault(
                ancestor_id,
                set(),
            ).add(node_id)

            current = current.parent

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        node_id = id(node)
        current: SceneObject | None = node

        while current is not None:
            ancestor_id = id(current)
            affected = self._by_ancestor.get(ancestor_id)

            if affected is not None:
                affected.discard(node_id)

                if not affected:
                    del self._by_ancestor[ancestor_id]

            current = current.parent

        self._depth_by_id.pop(
            node_id,
            None,
        )

    def affected_by(
        self,
        item: int | SceneObject,
        *,
        ordered: bool = False,
    ) -> tuple[int, ...]:
        node_id = item if isinstance(item, int) else id(item)

        affected = self._by_ancestor.get(
            node_id,
            (),
        )

        if not ordered:
            return tuple(affected)

        return tuple(
            sorted(
                affected,
                key=lambda affected_id: self._depth_by_id.get(
                    affected_id,
                    0,
                ),
            )
        )

    def depth_of(
        self,
        item: int | SceneObject,
    ) -> int:
        node_id = item if isinstance(item, int) else id(item)

        return self._depth_by_id.get(
            node_id,
            0,
        )


class SkinDependencyRegistry:
    """
    Tracks reverse skin dependencies by object id.

    joint_id -> affected Object3D ids

    Skin stores:

        Object3D -> Skin -> joints

    But dirty propagation needs the reverse direction:

        joint Node3D -> affected Object3D objects

    This registry does not own nodes, objects, or skins.
    It only stores ids.
    """

    def __init__(self) -> None:
        self._by_joint: dict[int, set[int]] = {}

    def register(
        self,
        object3d: Object3D,
    ) -> None:
        skin = object3d.skin

        if skin is None:
            return

        object_id = id(object3d)

        for joint in skin.joints:
            joint_id = id(joint)

            self._by_joint.setdefault(
                joint_id,
                set(),
            ).add(object_id)

    def unregister(
        self,
        object3d: Object3D,
    ) -> None:
        skin = object3d.skin

        if skin is None:
            return

        object_id = id(object3d)

        for joint in skin.joints:
            joint_id = id(joint)
            objects = self._by_joint.get(joint_id)

            if objects is None:
                continue

            objects.discard(object_id)

            if not objects:
                del self._by_joint[joint_id]

    def affected_by(
        self,
        item: int | Node3D,
    ) -> tuple[int, ...]:
        joint_id = item if isinstance(item, int) else id(item)

        return tuple(
            self._by_joint.get(
                joint_id,
                (),
            )
        )

    def affected_by_many(
        self,
        joint_ids: set[int],
    ) -> tuple[int, ...]:
        affected: set[int] = set()

        for joint_id in joint_ids:
            object_ids = self._by_joint.get(joint_id)

            if object_ids is None:
                continue

            affected.update(object_ids)

        return tuple(affected)






class SceneRegistry:
    """
    Tracks scene nodes by id, uid, render_id, tree dependencies,
    and skin dependencies.

    by_id is the only object source of truth.

    Secondary indexes store ids:

        by_uid: uid -> node_id
        by_render_id: render_id -> object_id
        tree: ancestor_id -> affected SceneObject ids
        skins: joint_id -> affected Object3D ids

    This class does not own the scene tree.
    It only indexes nodes that are already part of a Scene.
    """

    def __init__(self) -> None:
        self._next_render_id: int = 1

        self.by_id: dict[int, SceneObject] = {}
        self.by_uid: dict[str, int] = {}
        self.by_render_id: dict[int, int] = {}

        self.tree = TreeDependencyRegistry()
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
        self.register_id(node)

        if node.uid is not None:
            self.register_uid(node)

        self.tree.register(node)

        if node.is_object3d(node):
            self.register_render_id(node)
            self.skins.register(node)

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is not None:
            self.unregister_uid(node)

        self.tree.unregister(node)

        if node.is_object3d(node):
            self.skins.unregister(node)
            self.unregister_render_id(node)

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
        return self.by_id.get(node_id)

    def require_by_id(
        self,
        node_id: int,
    ) -> SceneObject:
        node = self.get_by_id(node_id)

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
        node_id = self.by_uid.get(uid)

        if node_id is None:
            return None

        return self.get_by_id(node_id)

    def require_by_uid(
        self,
        uid: str,
    ) -> SceneObject:
        node = self.get_by_uid(uid)

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

    def generate_render_id(self) -> int:
        render_id = self._next_render_id
        self._next_render_id += 1
        return render_id

    def get_by_render_id(
        self,
        render_id: int,
    ) -> Object3D | None:
        object_id = self.by_render_id.get(render_id)

        if object_id is None:
            return None

        node = self.get_by_id(object_id)

        if node is None:
            return None

        if not node.is_object3d(node):
            return None

        return cast(
            "Object3D",
            node,
        )

    def require_by_render_id(
        self,
        render_id: int,
    ) -> Object3D:
        object3d = self.get_by_render_id(render_id)

        if object3d is None:
            raise ValueError(
                f"Object3D render_id not found: {render_id!r}"
            )

        return object3d

    # =================================== #
    # Tree Dependency API
    # =================================== #

    @overload
    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: Literal[True],
        ordered: bool = False,
    ) -> tuple[int, ...]:
        ...

    @overload
    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: Literal[False] = False,
        ordered: bool = False,
    ) -> tuple[SceneObject, ...]:
        ...

    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: bool = False,
        ordered: bool = False,
    ) -> tuple[int, ...] | tuple[SceneObject, ...]:
        affected_ids = self.tree.affected_by(
            item,
            ordered=ordered,
        )

        if ids:
            return affected_ids

        affected: list[SceneObject] = []

        for node_id in affected_ids:
            node = self.get_by_id(node_id)

            if node is not None:
                affected.append(node)

        return tuple(affected)


    # =================================== #
    # Joint Dependency API
    # =================================== #
    @overload
    def affected_by_joint(
        self,
        item: int | Node3D,
        *,
        ids: Literal[True],
    ) -> tuple[int, ...]:
        ...

    @overload
    def affected_by_joint(
        self,
        item: int | Node3D,
        *,
        ids: Literal[False] = False,
    ) -> tuple[Object3D, ...]:
        ...

    def affected_by_joint(
        self,
        item: int | Node3D,
        *,
        ids: bool = False,
    ) -> tuple[int, ...] | tuple[Object3D, ...]:
        affected_ids = self.skins.affected_by(item)

        if ids:
            return affected_ids

        affected: list[Object3D] = []

        for object_id in affected_ids:
            node = self.get_by_id(object_id)

            if node is None:
                continue

            if not node.is_object3d(node):
                continue

            affected.append(
                cast(
                    "Object3D",
                    node,
                )
            )

        return tuple(affected)

    # =================================== #
    # Joint Dependency API
    # =================================== #
    @overload
    def affected_by_joints(
        self,
        items: set[int],
        *,
        ids: Literal[True],
    ) -> tuple[int, ...]:
        ...

    @overload
    def affected_by_joints(
        self,
        items: set[int],
        *,
        ids: Literal[False] = False,
    ) -> tuple[Object3D, ...]:
        ...

    def affected_by_joints(
        self,
        items: set[int],
        *,
        ids: bool = False,
    ) -> tuple[int, ...] | tuple[Object3D, ...]:
        affected_ids = self.skins.affected_by_many(items)

        if ids:
            return affected_ids

        affected: list[Object3D] = []

        for object_id in affected_ids:
            node = self.get_by_id(object_id)

            if node is None:
                continue

            if not node.is_object3d(node):
                continue

            affected.append(
                cast(
                    "Object3D",
                    node,
                )
            )

        return tuple(affected)


