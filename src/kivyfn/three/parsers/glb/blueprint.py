# kivyfn/three/parsers/glb/blueprint.py

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import cast

import numpy as np

from kivyfn.three.animations.binding import AnimationBinding
from kivyfn.three.animations.controller import AnimationController
from kivyfn.three.animations.library import AnimationLibrary
from kivyfn.three.animations.target import (
    BoneAnimationTarget,
    MultiBoneAnimationTarget,
    NodeAnimationTarget,
)
from kivyfn.three.animations.types import (
    AnimationTarget,
    AnimationTargetProtocol,
)
from kivyfn.three.graph.node import Node3D
from kivyfn.three.math.transform import Transform
from kivyfn.three.parsers.glb.instance import GlbInstance
from kivyfn.three.parsers.glb.node import GlbNode, GlbNodeFilter
from kivyfn.three.parsers.glb.scene import GlbScene
from kivyfn.three.parsers.glb.skin import GlbSkin
from kivyfn.three.skinning.skinned_model import SkinnedModel3D
from kivyfn.three.skinning.skinned_mesh import SkinnedMesh3D
from kivyfn.three.skinning.skeleton import Skeleton
from kivyfn.three.skinning.skin import Skin


@dataclass(slots=True)
class GlbNodeClassification:
    runtime_indices: set[int] = field(default_factory=set)
    skin_only_indices: set[int] = field(default_factory=set)
    skin_owner_indices: set[int] = field(default_factory=set)
    skin_node_indices_by_skin: dict[int, set[int]] = field(default_factory=dict)
    animated_targets: set[int] = field(default_factory=set)
    animated_skin_targets: set[int] = field(default_factory=set)
    animated_scene_targets: set[int] = field(default_factory=set)


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
    joint_indices: set[int] = field(default_factory=set)

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
        bone_bindings: dict[int, list[tuple[SkinnedModel3D, int]]] = {}

        classification = self._classify_nodes(
            glb_scene,
        )

        root = Node3D(
            name=instance_name or glb_scene.name or "Scene",
        )

        skip_indices = classification.skin_only_indices

        for node in glb_scene.roots:
            for child in node.instantiate(
                by_gltf_index=by_gltf_index,
                skip_indices=skip_indices,
                new_material=new_material,
            ):
                root.add_child(
                    child,
                )

        self._bind_skins(
            glb_scene=glb_scene,
            root=root,
            by_gltf_index=by_gltf_index,
            bone_bindings=bone_bindings,
        )

        animations = self._bind_animations(
            root=root,
            by_gltf_index=by_gltf_index,
            bone_bindings=bone_bindings,
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
        bone_bindings: dict[int, list[tuple[SkinnedModel3D, int]]],
    ) -> AnimationController | None:
        if self.animations is None or self.animations.is_empty:
            return None

        animated_targets: set[int] = {
            channel.target
            for clip in self.animations.clips.values()
            for channel in clip.channels
            if isinstance(channel.target, int)
        }

        targets: dict[AnimationTarget, AnimationTargetProtocol] = {}

        missing_targets: set[int] = set()

        for gltf_index in animated_targets:
            bindings = bone_bindings.get(
                gltf_index,
            )

            if bindings:
                grouped: dict[tuple[int, int], tuple[SkinnedModel3D, int]] = {}

                for model, bone_index in bindings:
                    group_key = (
                        id(model),
                        bone_index,
                    )

                    if group_key in grouped:
                        continue

                    grouped[group_key] = (
                        model,
                        bone_index,
                    )

                bone_targets = tuple(
                    BoneAnimationTarget(
                        model=model,
                        bone_index=bone_index,
                    )
                    for model, bone_index in grouped.values()
                )

                if len(bone_targets) == 1:
                    targets[gltf_index] = bone_targets[0]

                elif bone_targets:
                    targets[gltf_index] = MultiBoneAnimationTarget(
                        bone_targets,
                    )

                continue

            node = by_gltf_index.get(
                gltf_index,
            )

            if node is not None:
                targets[gltf_index] = NodeAnimationTarget(
                    node,
                )
                continue

            missing_targets.add(
                gltf_index,
            )


        return self.animations.bind(
            AnimationBinding(
                root=root,
                targets=targets,
            )
        )

    def _bind_skins(
        self,
        *,
        glb_scene: GlbScene,
        root: Node3D,
        by_gltf_index: dict[int, Node3D],
        bone_bindings: dict[int, list[tuple[SkinnedModel3D, int]]],
    ) -> None:
        model_cache: dict[int, SkinnedModel3D] = {}

        for glb_node in self._walk_scene(glb_scene):
            if glb_node.skin_index is None:
                continue

            owner_node = by_gltf_index.get(
                glb_node.gltf_index,
            )

            if owner_node is None:
                raise ValueError(
                    f"GLB node {glb_node.name!r} has a skin, but its "
                    f"runtime node was not instantiated."
                )

            meshes = self._skinned_meshs_of(
                owner_node,
            )

            if not meshes:
                raise ValueError(
                    f"GLB node {glb_node.name!r} has a skin, but no "
                    f"runtime SkinnedMesh3D was created for it."
                )

            model = model_cache.get(
                glb_node.skin_index,
            )

            if model is None:
                skin = self._create_skin(
                    glb_node=glb_node,
                    by_gltf_index=by_gltf_index,
                )

                model = SkinnedModel3D(
                    name=skin.name,
                    skin=skin,
                )
                root.add_child(model)

                model_cache[glb_node.skin_index] = model

                for bone_index, bone_gltf_index in enumerate(
                    model.skin.skeleton.bone_indices,
                ):
                    bone_bindings.setdefault(
                        bone_gltf_index,
                        [],
                    ).append(
                        (
                            model,
                            bone_index,
                        )
                    )

            for mesh in meshes:
                model.attach_skinned_mesh(
                    mesh,
                )

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

        animated_targets = (
            {
                channel.target
                for clip in self.animations.clips.values()
                for channel in clip.channels
                if isinstance(channel.target, int)
            }
            if self.animations is not None
            else set()
        )

        skeleton_indices: set[int] = set()

        def add_ancestors(
            node: GlbNode,
        ) -> None:
            current: GlbNode | None = node

            while current is not None:
                skeleton_indices.add(
                    current.gltf_index,
                )
                current = current.parent

        for joint_gltf_index in glb_skin.joint_indices:
            joint_node = self.nodes_by_index.get(
                joint_gltf_index,
            )

            if joint_node is None:
                raise ValueError(
                    f"GLB skin {glb_skin.name!r} used by node "
                    f"{glb_node.name!r} references joint node index "
                    f"{joint_gltf_index}, but that node was not loaded."
                )

            add_ancestors(
                joint_node,
            )

        for animated_gltf_index in animated_targets:
            animated_node = self.nodes_by_index.get(
                animated_gltf_index,
            )

            if animated_node is None:
                continue

            current: GlbNode | None = animated_node

            while current is not None:
                if current.gltf_index in skeleton_indices:
                    add_ancestors(
                        animated_node,
                    )
                    break

                current = current.parent

        ordered_bone_indices: list[int] = []

        def walk(
            node: GlbNode,
        ) -> None:
            if node.gltf_index in skeleton_indices:
                ordered_bone_indices.append(
                    node.gltf_index,
                )

            for child in node.children:
                walk(
                    child,
                )

        for scene in self.scenes:
            for scene_root in scene.roots:
                walk(
                    scene_root,
                )

        bone_lookup = {
            gltf_index: bone_index
            for bone_index, gltf_index in enumerate(
                ordered_bone_indices,
            )
        }

        bone_names: list[str] = []
        parent_bone_indices: list[int] = []
        bone_local_transforms: list[Transform] = []

        for bone_gltf_index in ordered_bone_indices:
            bone_node = self.nodes_by_index.get(
                bone_gltf_index,
            )

            if bone_node is None:
                raise ValueError(
                    f"Skin {glb_skin.name!r} references skeleton bone node index "
                    f"{bone_gltf_index}, but that node was not loaded."
                )

            bone_names.append(
                bone_node.name,
            )

            bone_local_transforms.append(
                bone_node.transform.copy(),
            )

            parent = bone_node.parent

            if parent is None:
                parent_bone_indices.append(
                    -1,
                )
            else:
                parent_bone_indices.append(
                    bone_lookup.get(
                        parent.gltf_index,
                        -1,
                    )
                )

        joint_names: list[str] = []
        joint_bone_indices: list[int] = []

        for joint_gltf_index in glb_skin.joint_indices:
            joint_node = self.nodes_by_index.get(
                joint_gltf_index,
            )

            if joint_node is None:
                raise ValueError(
                    f"GLB skin {glb_skin.name!r} references joint node index "
                    f"{joint_gltf_index}, but that node was not loaded."
                )

            joint_names.append(
                joint_node.name,
            )

            joint_bone_index = bone_lookup.get(
                joint_gltf_index,
            )

            if joint_bone_index is None:
                raise ValueError(
                    f"GLB skin {glb_skin.name!r} joint node index "
                    f"{joint_gltf_index} was not included in the skeleton graph."
                )

            joint_bone_indices.append(
                joint_bone_index,
            )

        skeleton = Skeleton(
            name=f"{glb_skin.name}.Skeleton",
            bone_names=tuple(
                bone_names,
            ),
            bone_indices=tuple(
                ordered_bone_indices,
            ),
            parent_bone_indices=np.asarray(
                parent_bone_indices,
                dtype=np.int32,
            ),
            bone_local_transforms=tuple(
                bone_local_transforms,
            ),
        )

        return Skin(
            name=glb_skin.name,
            skeleton=skeleton,
            joint_names=tuple(
                joint_names,
            ),
            joint_indices=glb_skin.joint_indices,
            joint_bone_indices=np.asarray(
                joint_bone_indices,
                dtype=np.int32,
            ),
            inverse_bind_matrices=glb_skin.inverse_bind_matrices,
        )

    def _classify_nodes(
        self,
        glb_scene: GlbScene,
    ) -> GlbNodeClassification:
        classification = GlbNodeClassification()

        animated_targets = (
            {
                channel.target
                for clip in self.animations.clips.values()
                for channel in clip.channels
                if isinstance(channel.target, int)
            }
            if self.animations is not None
            else set()
        )

        classification.animated_targets = animated_targets

        for glb_node in self._walk_scene(glb_scene):
            if glb_node.is_renderable:
                classification.runtime_indices.add(
                    glb_node.gltf_index,
                )

            if glb_node.skin_index is not None:
                classification.skin_owner_indices.add(
                    glb_node.gltf_index,
                )
                classification.runtime_indices.add(
                    glb_node.gltf_index,
                )

        for glb_node in self._walk_scene(glb_scene):
            if glb_node.skin_index is None:
                continue

            if glb_node.skin_index < 0 or glb_node.skin_index >= len(self.skins):
                raise ValueError(
                    f"GLB node {glb_node.name!r} references invalid skin index "
                    f"{glb_node.skin_index!r}."
                )

            glb_skin = self.skins[glb_node.skin_index]
            skin_indices = classification.skin_node_indices_by_skin.setdefault(
                glb_node.skin_index,
                set(),
            )

            def add_ancestors(
                node: GlbNode,
            ) -> None:
                current: GlbNode | None = node

                while current is not None:
                    skin_indices.add(
                        current.gltf_index,
                    )
                    current = current.parent

            for joint_gltf_index in glb_skin.joint_indices:
                joint_node = self.nodes_by_index.get(
                    joint_gltf_index,
                )

                if joint_node is None:
                    raise ValueError(
                        f"GLB skin {glb_skin.name!r} used by node "
                        f"{glb_node.name!r} references joint node index "
                        f"{joint_gltf_index}, but that node was not loaded."
                    )

                add_ancestors(
                    joint_node,
                )

            for animated_gltf_index in animated_targets:
                animated_node = self.nodes_by_index.get(
                    animated_gltf_index,
                )

                if animated_node is None:
                    continue

                current: GlbNode | None = animated_node

                while current is not None:
                    if current.gltf_index in skin_indices:
                        add_ancestors(
                            animated_node,
                        )
                        break

                    current = current.parent

        all_skin_node_indices: set[int] = set()

        for skin_indices in classification.skin_node_indices_by_skin.values():
            all_skin_node_indices.update(
                skin_indices,
            )

        classification.skin_only_indices = (
            all_skin_node_indices
            - classification.runtime_indices
        )

        classification.animated_skin_targets = (
            animated_targets
            & all_skin_node_indices
        )

        classification.animated_scene_targets = (
            animated_targets
            - all_skin_node_indices
        )

        return classification

    def _skinned_meshs_of(
        self,
        node: Node3D,
    ) -> list[SkinnedMesh3D]:
        if node.is_skinned_mesh:
            return [
                cast(SkinnedMesh3D, node),
            ]

        return [
            cast(SkinnedMesh3D, child)
            for child in node.children
            if child.is_skinned_mesh
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
    ) -> Iterator[GlbNode]:
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


