# kivyfn/three/graph/node_registry.py

from __future__ import annotations

from typing import Literal, overload, cast

from kivyfn.three.types import SceneObject
from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D


class TreeDependencyRegistry:
    """
    Tracks transform-tree dependencies by object id.

    ancestor_id -> affected SceneObject ids

    If an ancestor SceneObject changes transform, every affected
    SceneObject has a changed world matrix.

    This registry does not own nodes.
    It only stores ids.

    Hot-path guarantees:
    - affected_by(...) returns ids ordered parent-before-child.
    - compress_roots(...) removes dirty children covered by dirty parents.
    - affected_by_compressed(...) does not sort in the renderer path.
    """

    def __init__(
        self,
    ) -> None:
        self._by_ancestor: dict[int, set[int]] = {}

        self._ordered_by_ancestor: dict[int, tuple[int, ...]] = {}
        self._compressed_roots_cache: dict[frozenset[int], tuple[int, ...]] = {}
        self._compressed_affected_cache: dict[frozenset[int], tuple[int, ...]] = {}
        self._many_affected_cache: dict[frozenset[int], tuple[int, ...]] = {}

        self._depth_by_id: dict[int, int] = {}
        self._parent_by_id: dict[int, int | None] = {}
        self._ancestors_by_id: dict[int, tuple[int, ...]] = {}

        self._batch_depth: int = 0
        self._cache_dirty: bool = False

    # =================================== #
    # Cache
    # =================================== #

    def clear_cache(
        self,
    ) -> None:
        self._ordered_by_ancestor.clear()
        self._compressed_roots_cache.clear()
        self._compressed_affected_cache.clear()
        self._many_affected_cache.clear()

    def _invalidate_cache(
        self,
    ) -> None:
        if self._batch_depth > 0:
            self._cache_dirty = True
            return

        self.clear_cache()

    def _begin_batch(
        self,
    ) -> None:
        self._batch_depth += 1

    def _end_batch(
        self,
    ) -> None:
        self._batch_depth -= 1

        if self._batch_depth == 0 and self._cache_dirty:
            self._cache_dirty = False
            self.clear_cache()

    def clear(
        self,
    ) -> None:
        self._by_ancestor.clear()

        self._ordered_by_ancestor.clear()
        self._compressed_roots_cache.clear()
        self._compressed_affected_cache.clear()
        self._many_affected_cache.clear()

        self._depth_by_id.clear()
        self._parent_by_id.clear()
        self._ancestors_by_id.clear()

        self._batch_depth = 0
        self._cache_dirty = False

    # =================================== #
    # Register
    # =================================== #

    def register(
        self,
        node: SceneObject,
    ) -> None:
        node_id = id(node)

        if node_id in self._ancestors_by_id:
            self.unregister(node)

        ancestor_ids = self._compute_ancestor_ids(node)
        depth = len(ancestor_ids) - 1
        parent_id = ancestor_ids[1] if len(ancestor_ids) > 1 else None

        self._ancestors_by_id[node_id] = ancestor_ids
        self._depth_by_id[node_id] = depth
        self._parent_by_id[node_id] = parent_id

        for ancestor_id in ancestor_ids:
            self._by_ancestor.setdefault(
                ancestor_id,
                set(),
            ).add(node_id)

        self._invalidate_cache()

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        node_id = id(node)

        ancestor_ids = self._ancestors_by_id.pop(
            node_id,
            None,
        )

        if ancestor_ids is None:
            return

        for ancestor_id in ancestor_ids:
            affected = self._by_ancestor.get(
                ancestor_id,
            )

            if affected is None:
                continue

            affected.discard(
                node_id,
            )

            if not affected:
                del self._by_ancestor[ancestor_id]

        self._depth_by_id.pop(
            node_id,
            None,
        )
        self._parent_by_id.pop(
            node_id,
            None,
        )

        self._invalidate_cache()

    # =================================== #
    # Tree Register
    # =================================== #

    def register_tree(
        self,
        root: SceneObject,
    ) -> None:
        self._begin_batch()

        try:
            for node in root.walk(filter="all"):
                self.register(node)
        finally:
            self._end_batch()

    def unregister_tree(
        self,
        root: SceneObject,
    ) -> None:
        self._begin_batch()

        try:
            for node in root.walk(filter="all"):
                self.unregister(node)
        finally:
            self._end_batch()

    def rebuild_tree(
        self,
        root: SceneObject,
    ) -> None:
        self._begin_batch()

        try:
            self.unregister_tree(root)
            self.register_tree(root)
        finally:
            self._end_batch()

    # =================================== #
    # Query
    # =================================== #

    def depth_of(
        self,
        node_id: int,
    ) -> int:
        return self._depth_by_id.get(
            node_id,
            0,
        )

    def contains(
        self,
        node_id: int,
    ) -> bool:
        return node_id in self._depth_by_id

    def affected_by(
        self,
        ancestor_id: int,
    ) -> tuple[int, ...]:
        cached = self._ordered_by_ancestor.get(
            ancestor_id,
        )

        if cached is not None:
            return cached

        affected = self._by_ancestor.get(
            ancestor_id,
        )

        if not affected:
            result: tuple[int, ...] = ()
        else:
            result = tuple(
                sorted(
                    affected,
                    key=self.depth_of,
                )
            )

        self._ordered_by_ancestor[ancestor_id] = result
        return result

    def affected_by_many(
        self,
        ancestor_ids: set[int],
    ) -> tuple[int, ...]:
        if not ancestor_ids:
            return ()

        key = frozenset(ancestor_ids)

        cached = self._many_affected_cache.get(
            key,
        )

        if cached is not None:
            return cached

        affected: set[int] = set()

        for ancestor_id in key:
            affected.update(
                self._by_ancestor.get(
                    ancestor_id,
                    (),
                )
            )

        if not affected:
            result: tuple[int, ...] = ()
        else:
            result = tuple(
                sorted(
                    affected,
                    key=self.depth_of,
                )
            )

        self._many_affected_cache[key] = result
        return result

    def is_ancestor_of(
        self,
        ancestor_id: int,
        node_id: int,
    ) -> bool:
        affected = self._by_ancestor.get(
            ancestor_id,
        )

        if affected is None:
            return False

        return node_id in affected

    def compress_roots(
        self,
        node_ids: set[int],
    ) -> tuple[int, ...]:
        if not node_ids:
            return ()

        key = frozenset(node_ids)

        cached = self._compressed_roots_cache.get(
            key,
        )

        if cached is not None:
            return cached

        ordered = sorted(
            (
                node_id
                for node_id in key
                if node_id in self._depth_by_id
            ),
            key=self.depth_of,
        )

        roots: list[int] = []
        root_ids: set[int] = set()

        for node_id in ordered:
            parent_id = self._parent_by_id.get(
                node_id,
            )

            covered = False

            while parent_id is not None:
                if parent_id in root_ids:
                    covered = True
                    break

                parent_id = self._parent_by_id.get(
                    parent_id,
                )

            if covered:
                continue

            roots.append(node_id)
            root_ids.add(node_id)

        result = tuple(roots)
        self._compressed_roots_cache[key] = result
        return result

    def affected_by_compressed(
        self,
        node_ids: set[int],
    ) -> tuple[int, ...]:
        if not node_ids:
            return ()

        key = frozenset(node_ids)

        cached = self._compressed_affected_cache.get(
            key,
        )

        if cached is not None:
            return cached

        roots = self.compress_roots(
            node_ids,
        )

        if not roots:
            result: tuple[int, ...] = ()
            self._compressed_affected_cache[key] = result
            return result

        affected: list[int] = []

        for root_id in roots:
            affected.extend(
                self.affected_by(root_id)
            )

        result = tuple(affected)
        self._compressed_affected_cache[key] = result
        return result

    # =================================== #
    # Internal
    # =================================== #

    def _compute_ancestor_ids(
        self,
        node: SceneObject,
    ) -> tuple[int, ...]:
        ancestors: list[int] = []

        current: SceneObject | None = node

        while current is not None:
            ancestors.append(
                id(current),
            )
            current = current.parent

        return tuple(ancestors)



class SkinDependencyRegistry:
    """
    Tracks reverse skin dependencies by object id.

    joint_id -> affected Object3D ids

    This registry does not own nodes, objects, or skins.
    It only stores ids.
    """

    def __init__(
        self,
    ) -> None:
        self._by_joint: dict[int, set[int]] = {}
        self._by_object: dict[int, tuple[int, ...]] = {}

        self._affected_by_joint_cache: dict[int, tuple[int, ...]] = {}
        self._affected_by_many_cache: dict[frozenset[int], tuple[int, ...]] = {}

    # =================================== #
    # Cache
    # =================================== #

    def clear_cache(
        self,
    ) -> None:
        self._affected_by_joint_cache.clear()
        self._affected_by_many_cache.clear()

    def clear(
        self,
    ) -> None:
        self._by_joint.clear()
        self._by_object.clear()
        self.clear_cache()

    # =================================== #
    # Register
    # =================================== #

    def register(
        self,
        object3d: Object3D,
    ) -> None:
        object_id = id(object3d)

        if object_id in self._by_object:
            self.unregister(object3d)

        skin = object3d.skin

        if skin is None:
            return

        joint_ids = tuple(
            id(joint)
            for joint in skin.joints
        )

        if not joint_ids:
            return

        self._by_object[object_id] = joint_ids

        for joint_id in joint_ids:
            self._by_joint.setdefault(
                joint_id,
                set(),
            ).add(object_id)

        self.clear_cache()

    def unregister(
        self,
        object3d: Object3D,
    ) -> None:
        object_id = id(object3d)

        joint_ids = self._by_object.pop(
            object_id,
            None,
        )

        if joint_ids is None:
            return

        for joint_id in joint_ids:
            object_ids = self._by_joint.get(
                joint_id,
            )

            if object_ids is None:
                continue

            object_ids.discard(
                object_id,
            )

            if not object_ids:
                del self._by_joint[joint_id]

        self.clear_cache()

    # =================================== #
    # Query
    # =================================== #

    def contains_object(
        self,
        object_id: int,
    ) -> bool:
        return object_id in self._by_object

    def contains_joint(
        self,
        joint_id: int,
    ) -> bool:
        return joint_id in self._by_joint

    def joints_of(
        self,
        object3d: Object3D | int,
    ) -> tuple[int, ...]:
        object_id = object3d if isinstance(object3d, int) else id(object3d)

        return self._by_object.get(
            object_id,
            (),
        )

    def affected_by(
        self,
        item: Node3D | int,
    ) -> tuple[int, ...]:
        joint_id = item if isinstance(item, int) else id(item)

        cached = self._affected_by_joint_cache.get(
            joint_id,
        )

        if cached is not None:
            return cached

        result = tuple(
            self._by_joint.get(
                joint_id,
                (),
            )
        )

        self._affected_by_joint_cache[joint_id] = result
        return result

    def affected_by_many(
        self,
        joint_ids: set[int],
    ) -> tuple[int, ...]:
        if not joint_ids:
            return ()

        key = frozenset(joint_ids)

        cached = self._affected_by_many_cache.get(
            key,
        )

        if cached is not None:
            return cached

        affected: set[int] = set()

        for joint_id in key:
            affected.update(
                self._by_joint.get(
                    joint_id,
                    (),
                )
            )

        result = tuple(affected)
        self._affected_by_many_cache[key] = result
        return result




class SceneRegistry:
    """
    Tracks scene nodes by id, uid, render_id, tree dependencies,
    object ids, and skin dependencies.

    by_id is the only object source of truth.

    Secondary indexes store ids:

        by_uid: uid -> node_id
        by_render_id: render_id -> object_id
        object_ids: set[object_id]
        tree: ancestor_id -> affected SceneObject ids
        skins: joint_id -> affected Object3D ids

    This class does not own the scene tree.
    It only indexes nodes that are already part of a Scene.
    """

    def __init__(
        self,
    ) -> None:
        self._next_render_id: int = 1

        self.by_id: dict[int, SceneObject] = {}
        self.by_uid: dict[str, int] = {}
        self.by_render_id: dict[int, int] = {}
        self.object_ids: set[int] = set()

        self.tree = TreeDependencyRegistry()
        self.skins = SkinDependencyRegistry()

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
        self._register_node_indexes(node)
        self.tree.register(node)

    def unregister(
        self,
        node: SceneObject,
    ) -> None:
        self.tree.unregister(node)
        self._unregister_node_indexes(node)

    def register_tree(
        self,
        root: SceneObject,
    ) -> None:
        nodes = tuple(
            root.walk(
                filter="all",
            )
        )

        for node in nodes:
            self._register_node_indexes(node)

        self.tree.register_tree(root)

    def unregister_tree(
        self,
        root: SceneObject,
    ) -> None:
        nodes = tuple(
            root.walk(
                filter="all",
            )
        )

        self.tree.unregister_tree(root)

        for node in nodes:
            self._unregister_node_indexes(node)

    def rebuild_tree(
        self,
        root: SceneObject,
    ) -> None:
        self.unregister_tree(root)
        self.register_tree(root)

    def clear(
        self,
    ) -> None:
        self._next_render_id = 1

        self.by_id.clear()
        self.by_uid.clear()
        self.by_render_id.clear()
        self.object_ids.clear()

        self.tree.clear()
        self.skins.clear()

    # =================================== #
    # Internal Node Indexing
    # =================================== #

    def _register_node_indexes(
        self,
        node: SceneObject,
    ) -> None:
        self.register_id(node)

        if node.uid is not None:
            self.register_uid(node)

        if node.is_object:
            object3d = cast(Object3D, node)
            object_id = id(object3d)

            self.object_ids.add(object_id)
            self.register_render_id(object3d)
            self.skins.register(object3d)

    def _unregister_node_indexes(
        self,
        node: SceneObject,
    ) -> None:
        if node.uid is not None:
            self.unregister_uid(node)

        if node.is_object:
            object3d = cast(Object3D, node)
            object_id = id(object3d)

            self.skins.unregister(object3d)
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

    def contains_id(
        self,
        node_id: int,
    ) -> bool:
        return node_id in self.by_id

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

    def generate_render_id(
        self,
    ) -> int:
        render_id = self._next_render_id
        self._next_render_id += 1
        return render_id

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

    # =================================== #
    # Hot Type Queries
    # =================================== #

    def is_object_id(
        self,
        node_id: int,
    ) -> bool:
        return node_id in self.object_ids

    def is_joint_id(
        self,
        node_id: int,
    ) -> bool:
        return self.skins.contains_joint(
            node_id,
        )

    def object_by_id(
        self,
        node_id: int,
    ) -> Object3D | None:
        if node_id not in self.object_ids:
            return None

        node = self.get_by_id(
            node_id,
        )

        if node is None:
            return None

        return cast(
            Object3D,
            node,
        )

    # =================================== #
    # Tree Dependency API
    # =================================== #

    @overload
    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: Literal[True],
    ) -> tuple[int, ...]:
        ...

    @overload
    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: Literal[False] = False,
    ) -> tuple[SceneObject, ...]:
        ...

    def affected_by_tree(
        self,
        item: int | SceneObject,
        *,
        ids: bool = False,
    ) -> tuple[int, ...] | tuple[SceneObject, ...]:
        node_id = item if isinstance(item, int) else id(item)

        affected_ids = self.tree.affected_by(
            node_id,
        )

        if ids:
            return affected_ids

        return tuple(
            node
            for affected_id in affected_ids
            if (node := self.get_by_id(affected_id)) is not None
        )

    @overload
    def affected_by_compressed_tree(
        self,
        items: set[int],
        *,
        ids: Literal[True],
    ) -> tuple[int, ...]:
        ...

    @overload
    def affected_by_compressed_tree(
        self,
        items: set[int],
        *,
        ids: Literal[False] = False,
    ) -> tuple[SceneObject, ...]:
        ...

    def affected_by_compressed_tree(
        self,
        items: set[int],
        *,
        ids: bool = False,
    ) -> tuple[int, ...] | tuple[SceneObject, ...]:
        affected_ids = self.tree.affected_by_compressed(
            items,
        )

        if ids:
            return affected_ids

        return tuple(
            node
            for affected_id in affected_ids
            if (node := self.get_by_id(affected_id)) is not None
        )

    def compress_tree_roots(
        self,
        items: set[int],
    ) -> tuple[int, ...]:
        return self.tree.compress_roots(
            items,
        )

    def depth_of(
        self,
        node_id: int,
    ) -> int:
        return self.tree.depth_of(
            node_id,
        )

    # =================================== #
    # Skin Dependency API
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
        affected_ids = self.skins.affected_by(
            item,
        )

        if ids:
            return affected_ids

        return tuple(
            object3d
            for object_id in affected_ids
            if (object3d := self.object_by_id(object_id)) is not None
        )

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
        affected_ids = self.skins.affected_by_many(
            items,
        )

        if ids:
            return affected_ids

        return tuple(
            object3d
            for object_id in affected_ids
            if (object3d := self.object_by_id(object_id)) is not None
        )

    def joints_of(
        self,
        object3d: Object3D | int,
    ) -> tuple[int, ...]:
        return self.skins.joints_of(
            object3d,
        )


