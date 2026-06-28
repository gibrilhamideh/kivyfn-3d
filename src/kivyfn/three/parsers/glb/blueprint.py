# kivyfn/three/parsers/glb/blueprint.py

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import cast

from kivyfn.three.graph.node import Node3D
from kivyfn.three.assets.object3d import Object3D
from kivyfn.three.assets.skin import Skin
from kivyfn.three.parsers.glb.instance import GlbInstance
from kivyfn.three.parsers.glb.node import GlbNode, GlbNodeFilter
from kivyfn.three.parsers.glb.scene import GlbScene
from kivyfn.three.parsers.glb.skin import GlbSkin
from kivyfn.three.animations.controller import AnimationController
from kivyfn.three.animations.library import AnimationLibrary
from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.types import AnimationTarget


@dataclass(slots=True)
class GlbBlueprint:
    """
    Parsed reusable GLB template.

    This is asset-level data. It does not own runtime scene nodes.
    instantiate() creates a GlbInstance with its own runtime node map.
    """

    scenes: list[GlbScene] = field(default_factory=list)

    nodes_by_index: dict[int, GlbNode] = field(default_factory=dict)
    nodes_by_name: dict[str, GlbNode] = field(default_factory=dict)
    skins: list[GlbSkin] = field(default_factory=list)

    animations: AnimationLibrary | None = None

    # Set by parser after scenes are loaded.
    default_scene: GlbScene = field(init=False)

    def instantiate(
        self,
        scene: int | GlbScene | None = None,
        *,
        instance_name: str = "",
        new_material: bool = True,
    ) -> GlbInstance:
        glb_scene = self._resolve_scene(scene)

        by_gltf_index: dict[int, Node3D] = {}

        root = Node3D(
            name=instance_name or glb_scene.name or "Scene",
        )

        for node in glb_scene.roots:
            root.add_child(
                node.instantiate(
                    by_gltf_index=by_gltf_index,
                    new_material=new_material,
                )
            )

        self._bind_skins(
            glb_scene=glb_scene,
            by_gltf_index=by_gltf_index,
        )

        animations = self._bind_animations(
            root=root,
            by_gltf_index=by_gltf_index,
        )

        return GlbInstance(
            root=root,
            by_gltf_index=by_gltf_index,
            animations=animations,
        )

    def set_default_scene(
        self,
        scene: GlbScene,
    ) -> None:
        if not any(
            candidate is scene
            for candidate in self.scenes
        ):
            raise ValueError(
                "Default GLB scene must belong to this blueprint."
            )

        self.default_scene = scene

    def _resolve_scene(
        self,
        scene: int | GlbScene | None,
    ) -> GlbScene:
        if not self.scenes:
            raise ValueError(
                "Cannot instantiate GLB: no scenes were loaded."
            )

        if scene is None:
            try:
                return self.default_scene

            except AttributeError as error:
                raise ValueError(
                    "Cannot instantiate GLB: default scene was not set."
                ) from error

        if isinstance(scene, GlbScene):
            if not any(
                candidate is scene
                for candidate in self.scenes
            ):
                raise ValueError(
                    "GLB scene does not belong to this blueprint."
                )

            return scene

        if scene < 0 or scene >= len(self.scenes):
            raise ValueError(
                f"GLB scene index does not exist: {scene!r}. "
                f"Available scenes: 0..{len(self.scenes) - 1}."
            )

        return self.scenes[scene]

    def _bind_animations(
        self,
        *,
        root: Node3D,
        by_gltf_index: dict[int, Node3D],
    ) -> AnimationController | None:
        if self.animations is None or self.animations.is_empty:
            return None

        return self.animations.bind(
            AnimationBinding(
                root=root,
                targets=cast(
                    dict[AnimationTarget, Node3D],
                    by_gltf_index,
                ),
            )
        )

    def _bind_skins(
        self,
        *,
        glb_scene: GlbScene,
        by_gltf_index: dict[int, Node3D],
    ) -> None:
        for glb_node in self._walk_scene(glb_scene):
            if glb_node.skin_index is None:
                continue

            owner_node = by_gltf_index.get(glb_node.gltf_index)

            if owner_node is None:
                raise ValueError(
                    f"GLB node {glb_node.name!r} has a skin, but its "
                    f"runtime node was not instantiated."
                )

            objects = self._objects_of_node(owner_node)

            if not objects:
                raise ValueError(
                    f"GLB node {glb_node.name!r} has a skin, but no "
                    f"runtime Object3D was created for it."
                )

            skin = self._create_skin(
                glb_node=glb_node,
                by_gltf_index=by_gltf_index,
            )

            for obj in objects:
                obj.set_skin(skin)



    def _create_skin(
        self,
        *,
        glb_node: GlbNode,
        by_gltf_index: dict[int, Node3D],
    ) -> Skin:
        if glb_node.skin_index is None:
            raise ValueError(
                f"GLB node {glb_node.name!r} has no skin index."
            )

        if glb_node.skin_index < 0 or glb_node.skin_index >= len(self.skins):
            raise ValueError(
                f"GLB node {glb_node.name!r} references invalid skin index "
                f"{glb_node.skin_index!r}."
            )

        glb_skin = self.skins[glb_node.skin_index]

        joints: list[Node3D] = []

        for joint_index in glb_skin.joint_indices:
            joint = by_gltf_index.get(joint_index)

            if joint is None:
                raise ValueError(
                    f"GLB skin {glb_skin.name!r} used by node "
                    f"{glb_node.name!r} references joint node index "
                    f"{joint_index}, but that node was not instantiated "
                    f"in this GlbInstance."
                )

            joints.append(joint)

        return Skin(
            name=glb_skin.name,
            joints=tuple(joints),
            inverse_bind_matrices=glb_skin.inverse_bind_matrices,
        )

    def _objects_of_node(
        self,
        node: Node3D,
    ) -> list[Object3D]:
        if node.is_object:
            return [
                cast(Object3D, node)
            ]

        return [
            cast(Object3D, child)
            for child in node.children
            if child.is_object
        ]

    # =================================== #
    # Lookup
    # =================================== #

    def find(
        self,
        name: str,
    ) -> GlbNode | None:
        return self.nodes_by_name.get(name)

    def require(
        self,
        name: str,
    ) -> GlbNode:
        node = self.find(name)

        if node is None:
            raise ValueError(f"GlbNode not found: {name!r}")

        return node

    # =================================== #
    # Traversal
    # =================================== #

    def walk(self) -> Iterator[GlbNode]:
        seen: set[int] = set()

        for scene in self.scenes:
            for root in scene.roots:
                for node in root.walk():
                    if node.gltf_index in seen:
                        continue

                    seen.add(node.gltf_index)
                    yield node

    def renderables(self) -> Iterator[GlbNode]:
        for node in self.walk():
            if node.is_renderable:
                yield node

    def _walk_scene(
        self,
        scene: GlbScene,
    ):
        for root in scene.roots:
            yield from root.walk()

    # =================================== #
    # Tags
    # =================================== #

    def tag(
        self,
        tag: str,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for scene in self.scenes:
            for root in scene.roots:
                root.tag(
                    tag,
                    include=include,
                    exclude=exclude,
                )

    def untag(
        self,
        tag: str,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for scene in self.scenes:
            for root in scene.roots:
                root.untag(
                    tag,
                    include=include,
                    exclude=exclude,
                )

    def clear_tags(
        self,
        *,
        include: GlbNodeFilter | None = None,
        exclude: GlbNodeFilter | None = None,
    ) -> None:
        for scene in self.scenes:
            for root in scene.roots:
                root.clear_tags(
                    include=include,
                    exclude=exclude,
                )

    def __repr__(self) -> str:
        try:
            default_scene_name = self.default_scene.name

        except AttributeError:
            default_scene_name = "<unset>"

        return (
            "GlbBlueprint(\n"
            f"  nodes={len(self.nodes_by_index)},\n"
            f"  scenes={len(self.scenes)},\n"
            f"  default_scene={default_scene_name!r}\n"
            ")"
        )


