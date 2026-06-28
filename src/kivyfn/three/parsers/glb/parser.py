# kivyfn/three/parsers/glb/parser.py

from __future__ import annotations

import base64
import os
import xxhash
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

import numpy as np
from pygltflib import GLTF2

from kivyfn.three.types import MeshMode
from kivyfn.three.math.matrix import Matrix3
from kivyfn.three.math.matrix import Matrix4
from kivyfn.three.math.quaternion import Quaternion
from kivyfn.three.math.transform import Transform
from kivyfn.three.math.vector import Vector3
from kivyfn.three.assets.geometry import Geometry, GeometryBounds, MorphTarget
from kivyfn.three.assets.material import Material
from kivyfn.three.animations.channel import AnimationChannel
from kivyfn.three.animations.clip import AnimationClip
from kivyfn.three.animations.keyframe import AnimationKeyframe
from kivyfn.three.animations.library import AnimationLibrary
from kivyfn.three.animations.sampler import AnimationSampler
from kivyfn.three.animations.types import (
    AnimationPath,
    AnimationValue,
    InterpolationMode,
)
from kivyfn.three.parsers.glb.blueprint import (
    GlbBlueprint,
    GlbAsset,
    GlbPrimitive,
)
from kivyfn.three.graphics.gl.texture import (
    Texture2D,
    TextureWrap,
    TextureMinFilter,
    TextureMagFilter,
)


@dataclass(slots=True)
class GlbNodeData:
    raw: Any

    @property
    def name(self) -> str | None:
        return getattr(self.raw, "name", None)

    @property
    def mesh_index(self) -> int | None:
        return getattr(self.raw, "mesh", None)

    @property
    def children(self) -> list[int]:
        return list(getattr(self.raw, "children", None) or [])

    @property
    def matrix(self) -> list[float] | None:
        return getattr(self.raw, "matrix", None)

    @property
    def translation(self) -> list[float] | None:
        return getattr(self.raw, "translation", None)

    @property
    def rotation(self) -> list[float] | None:
        return getattr(self.raw, "rotation", None)

    @property
    def scale(self) -> list[float] | None:
        return getattr(self.raw, "scale", None)

    @property
    def extras(self) -> dict[str, object]:
        return dict(getattr(self.raw, "extras", None) or {})


@dataclass(slots=True)
class GlbPrimitiveData:
    raw: Any

    @property
    def attributes(self) -> Any:
        return self.raw.attributes

    @property
    def position_index(self) -> int | None:
        return getattr(self.attributes, "POSITION", None)

    @property
    def normal_index(self) -> int | None:
        return getattr(self.attributes, "NORMAL", None)

    @property
    def uv_index(self) -> int | None:
        return getattr(self.attributes, "TEXCOORD_0", None)

    @property
    def tangent_index(self) -> int | None:
        return getattr(self.attributes, "TANGENT", None)

    @property
    def joints_index(self) -> int | None:
        return getattr(self.attributes, "JOINTS_0", None)

    @property
    def weights_index(self) -> int | None:
        return getattr(self.attributes, "WEIGHTS_0", None)

    @property
    def indices_index(self) -> int | None:
        return getattr(self.raw, "indices", None)

    @property
    def material_index(self) -> int | None:
        return getattr(self.raw, "material", None)

    @property
    def extras(self) -> dict[str, object]:
        return dict(getattr(self.raw, "extras", None) or {})

    @property
    def mode(self) -> int:
        return int(getattr(self.raw, "mode", 4) or 4)

    @property
    def targets(self) -> list[Any]:
        return list(getattr(self.raw, "targets", None) or [])



@dataclass(slots=True)
class GlbMaterialData:
    raw: Any

    @property
    def name(self) -> str | None:
        return getattr(self.raw, "name", None)

    @property
    def pbr(self) -> Any:
        return getattr(self.raw, "pbrMetallicRoughness", None)

    @property
    def emissive_factor(self) -> list[float] | None:
        return getattr(self.raw, "emissiveFactor", None)

    @property
    def normal_texture(self) -> Any:
        return getattr(self.raw, "normalTexture", None)

    @property
    def emissive_texture(self) -> Any:
        return getattr(self.raw, "emissiveTexture", None)

    @property
    def occlusion_texture(self) -> Any:
        return getattr(self.raw, "occlusionTexture", None)

    @property
    def extras(self) -> dict[str, object]:
        return dict(getattr(self.raw, "extras", None) or {})


@dataclass(slots=True)
class GlbAnimationData:
    raw: Any

    @property
    def name(self) -> str | None:
        return getattr(self.raw, "name", None)

    @property
    def channels(self) -> list[Any]:
        return list(getattr(self.raw, "channels", None) or [])

    @property
    def samplers(self) -> list[Any]:
        return list(getattr(self.raw, "samplers", None) or [])


@dataclass(slots=True)
class GlbAnimationChannelData:
    raw: Any

    @property
    def sampler_index(self) -> int:
        return int(getattr(self.raw, "sampler"))

    @property
    def target(self) -> Any:
        return getattr(self.raw, "target")

    @property
    def target_node_index(self) -> int | None:
        target = self.target
        if target is None:
            return None

        return getattr(target, "node", None)

    @property
    def target_path(self) -> str | None:
        target = self.target
        if target is None:
            return None

        return getattr(target, "path", None)


@dataclass(slots=True)
class GlbAnimationSamplerData:
    raw: Any

    @property
    def input_index(self) -> int | None:
        return getattr(self.raw, "input", None)

    @property
    def output_index(self) -> int | None:
        return getattr(self.raw, "output", None)

    @property
    def interpolation(self) -> str:
        return str(getattr(self.raw, "interpolation", None) or "LINEAR")

class GlbParser:
    _DTYPE_MAP: ClassVar[dict[int, Any]] = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }

    _COMPONENT_COUNT_MAP: ClassVar[dict[str, int]] = {
        "SCALAR": 1,
        "VEC2": 2,
        "VEC3": 3,
        "VEC4": 4,
        "MAT2": 4,
        "MAT3": 9,
        "MAT4": 16,
    }

    _SAMPLER_MIN_FILTER_MAP: ClassVar[dict[int, TextureMinFilter]] = {
        9728: "nearest",
        9729: "linear",
        9984: "nearest_mipmap_nearest",
        9985: "linear_mipmap_nearest",
        9986: "nearest_mipmap_linear",
        9987: "linear_mipmap_linear",
    }

    _SAMPLER_MAG_FILTER_MAP: ClassVar[dict[int, TextureMagFilter]] = {
        9728: "nearest",
        9729: "linear",
    }

    _SAMPLER_WRAP_MAP: ClassVar[dict[int, TextureWrap]] = {
        33071: "clamp_to_edge",
        33648: "mirrored_repeat",
        10497: "repeat",
    }

    _GLTF_MODE_MAP: ClassVar[dict[int, MeshMode]] = {
        0: "points",
        1: "lines",
        2: "line_loop",
        3: "line_strip",
        4: "triangles",
        5: "triangle_strip",
        6: "triangle_fan",
    }

    _MIME_EXTENSION_MAP: ClassVar[dict[str, str]] = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }


    def __init__(
        self,
        flip_v: bool = False,
        flip_winding: bool = False,
    ):


        self.blueprint: GlbBlueprint

        self.flip_v = flip_v
        self.flip_winding = flip_winding

        self._gltf: Any = None
        self._buffer_bytes: bytes | None = None
        self._base_path: Path | None = None

        self._texture_cache: dict[int, Texture2D] = {}
        self._image_bytes_cache: dict[int, tuple[bytes, str]] = {}
        self._image_texture_cache: dict[
            tuple[str, int | None, int | None, int | None, int | None],
            Texture2D,
        ] = {}

    def parse(
        self,
        filename: str | Path,
    ) -> GlbBlueprint:
        path = Path(filename)

        self.blueprint: GlbBlueprint = GlbBlueprint()

        self._gltf = GLTF2().load_binary(str(path))
        self._buffer_bytes = self._load_buffer_bytes(path)
        self._base_path = path.parent

        self._texture_cache.clear()
        self._image_bytes_cache.clear()
        self._image_texture_cache.clear()

        for root_index in self._get_scene_root_indices():
            root_blueprint = self._load_node(root_index)
            self.blueprint.tree.append(root_blueprint)

        self.blueprint.animations = self._load_animations()

        return self.blueprint

    # =================================== #
    # Scene / Node Tree
    # =================================== #

    def _get_scene_root_indices(self) -> list[int]:
        if self._gltf.scenes and self._gltf.scene is not None:
            scene = self._gltf.scenes[self._gltf.scene]
            return list(scene.nodes or [])

        nodes = self._gltf.nodes or []
        child_indices: set[int] = set()

        for raw_node in nodes:
            node = GlbNodeData(raw_node)
            child_indices.update(node.children)

        return [
            index
            for index in range(len(nodes))
            if index not in child_indices
        ]

    def _load_node(
        self,
        node_index: int,
    ) -> GlbAsset:
        node = GlbNodeData(self._gltf.nodes[node_index])

        node_name = self._get_node_name(
            node_index=node_index,
            node=node,
        )

        primitives = self._get_node_primitives(node)
        local_transform = self._get_node_local_transform(node)

        asset = GlbAsset(
            name=node_name,
            gltf_index=node_index,
            transform=local_transform,
            extras=node.extras.copy(),
        )

        self._register_asset(asset)

        for primitive_index, primitive in enumerate(primitives):
            primitive_name = node_name

            if len(primitives) > 1:
                primitive_name = self._make_unique_name(
                    f"{node_name}.{primitive_index:03d}"
                )

            geometry = self._process_primitive_geometry(primitive)
            if geometry is None:
                continue

            geometry.name = primitive_name

            material = self._process_material(
                primitive=primitive,
                fallback_name=primitive_name,
            )

            asset.primitives.append(
                GlbPrimitive(
                    name=primitive_name,
                    geometry=geometry,
                    material=material,
                    extras=primitive.extras.copy(),
                )
            )

        for child_index in node.children:
            child_asset = self._load_node(child_index)
            asset.children.append(child_asset)

        return asset

    def _get_node_name(
        self,
        node_index: int,
        node: GlbNodeData,
    ) -> str:
        mesh_name = None

        if node.mesh_index is not None:
            mesh = self._gltf.meshes[node.mesh_index]
            mesh_name = getattr(mesh, "name", None)

        name = (
            node.name
            or mesh_name
            or f"node_{node_index}"
        )

        return self._make_unique_name(name)

    def _make_unique_name(
        self,
        name: str,
    ) -> str:
        if name not in self.blueprint.assets:
            return name

        counter = 1

        while True:
            candidate = f"{name}.{counter:03d}"

            if candidate not in self.blueprint.assets:
                return candidate

            counter += 1

    def _register_asset(
        self,
        asset: GlbAsset,
    ) -> None:
        self.blueprint.assets[asset.name] = asset

    def _get_node_primitives(
        self,
        node: GlbNodeData,
    ) -> list[GlbPrimitiveData]:
        if node.mesh_index is None:
            return []

        mesh = self._gltf.meshes[node.mesh_index]

        return [
            GlbPrimitiveData(raw_primitive)
            for raw_primitive in list(mesh.primitives or [])
        ]

    # =================================== #
    # Node Transforms
    # =================================== #

    def _get_node_local_transform(
        self,
        node: GlbNodeData,
    ) -> Transform:
        if node.matrix:
            matrix = Matrix4(
                np.array(
                    node.matrix,
                    dtype=np.float32,
                ).reshape((4, 4))
            )

            return self._transform_from_matrix4(matrix)

        translation_data = node.translation
        rotation_data = node.rotation
        scale_data = node.scale

        translation = (
            Vector3(
                float(translation_data[0]),
                float(translation_data[1]),
                float(translation_data[2]),
            )
            if translation_data is not None
            else Vector3(0.0, 0.0, 0.0)
        )

        rotation = (
            Quaternion(
                float(rotation_data[0]),
                float(rotation_data[1]),
                float(rotation_data[2]),
                float(rotation_data[3]),
            )
            if rotation_data is not None
            else Quaternion.identity()
        )

        scale = (
            Vector3(
                float(scale_data[0]),
                float(scale_data[1]),
                float(scale_data[2]),
            )
            if scale_data is not None
            else Vector3(1.0, 1.0, 1.0)
        )

        return Transform(
            translation=translation,
            rotation=rotation,
            scale=scale,
        )

    def _transform_from_matrix4(
        self,
        matrix: Matrix4,
    ) -> Transform:
        values = matrix.values

        translation = Vector3(
            float(values[0, 3]),
            float(values[1, 3]),
            float(values[2, 3]),
        )

        scale = Vector3(
            float(np.linalg.norm(values[:3, 0])),
            float(np.linalg.norm(values[:3, 1])),
            float(np.linalg.norm(values[:3, 2])),
        )

        rotation_values = values[:3, :3].copy()

        if scale.x != 0.0:
            rotation_values[:, 0] /= scale.x

        if scale.y != 0.0:
            rotation_values[:, 1] /= scale.y

        if scale.z != 0.0:
            rotation_values[:, 2] /= scale.z

        rotation = Quaternion.from_matrix3(
            Matrix3(
                rotation_values.astype(
                    np.float32,
                    copy=False,
                )
            )
        )

        return Transform(
            translation=translation,
            rotation=rotation,
            scale=scale,
        )

    # =================================== #
    # Animations
    # =================================== #
    def _load_animations(self) -> AnimationLibrary | None:
        raw_animations = list(self._gltf.animations or [])

        if not raw_animations:
            return None

        library = AnimationLibrary()

        for animation_index, raw_animation in enumerate(raw_animations):
            animation = GlbAnimationData(raw_animation)

            clip_name = (
                animation.name
                or f"animation_{animation_index}"
            )

            channels: list[AnimationChannel] = []

            for raw_channel in animation.channels:
                channel = GlbAnimationChannelData(raw_channel)

                if channel.target_node_index is None:
                    continue

                target_path = channel.target_path
                if target_path not in {
                    "translation",
                    "rotation",
                    "scale",
                    "weights",
                }:
                    continue

                path = cast(AnimationPath, target_path)

                if channel.sampler_index < 0:
                    continue

                if channel.sampler_index >= len(animation.samplers):
                    continue

                sampler_data = GlbAnimationSamplerData(
                    animation.samplers[channel.sampler_index]
                )

                sampler = self._load_animation_sampler(
                    sampler=sampler_data,
                    path=path,
                )

                if sampler is None:
                    continue

                channels.append(
                    AnimationChannel(
                        target=channel.target_node_index,
                        path=path,
                        sampler=sampler,
                    )
                )

            if not channels:
                continue

            library.add(
                AnimationClip(
                    name=clip_name,
                    channels=tuple(channels),
                )
            )

        if library.is_empty:
            return None

        return library

    def _load_animation_sampler(
        self,
        sampler: GlbAnimationSamplerData,
        path: AnimationPath,
    ) -> AnimationSampler | None:
        times = self._read_accessor(sampler.input_index)
        values = self._read_accessor(sampler.output_index)

        if times is None or values is None:
            return None

        times = times.reshape(-1).astype(
            np.float32,
            copy=False,
        )

        if len(times) == 0:
            return None

        interpolation_name = sampler.interpolation.upper()

        interpolation = self._animation_interpolation_to_mode(
            interpolation_name,
        )

        keyframes: list[AnimationKeyframe] = []

        # First version: ignore glTF CUBICSPLINE tangents.
        # CUBICSPLINE output layout is:
        #   in_tangent, value, out_tangent
        # per keyframe.
        if interpolation_name == "CUBICSPLINE":
            if len(values) != len(times) * 3:
                return None

            values = values.reshape(len(times), 3, -1)[:, 1, :]

        if len(values) != len(times):
            return None

        for index, time in enumerate(times):
            value = self._animation_value_from_row(
                row=values[index],
                path=path,
            )

            if value is None:
                continue

            keyframes.append(
                AnimationKeyframe(
                    time=float(time),
                    value=value,
                )
            )

        if not keyframes:
            return None

        return AnimationSampler(
            keyframes=tuple(keyframes),
            interpolation=interpolation,
        )

    def _animation_interpolation_to_mode(
        self,
        value: str,
    ) -> InterpolationMode:
        match value.upper():
            case "STEP":
                return "step"

            case "LINEAR":
                return "linear"

            case "CUBICSPLINE":
                # First version: we strip tangents and sample as linear.
                return "linear"

            case _:
                return "linear"

    def _animation_value_from_row(
        self,
        *,
        row: np.ndarray,
        path: AnimationPath,
    ) -> AnimationValue | None:
        match path:
            case "translation":
                if row.shape[0] < 3:
                    return None

                return Vector3(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                )

            case "rotation":
                if row.shape[0] < 4:
                    return None

                return Quaternion(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                ).normalize()

            case "scale":
                if row.shape[0] < 3:
                    return None

                return Vector3(
                    float(row[0]),
                    float(row[1]),
                    float(row[2]),
                )

            case "weights":
                return tuple(float(value) for value in row.reshape(-1))

    # =================================== #
    # Materials
    # =================================== #

    def _process_material(
        self,
        primitive: GlbPrimitiveData,
        fallback_name: str,
    ) -> Material:
        material_index = primitive.material_index

        if (
            material_index is None
            or not self._gltf.materials
            or material_index < 0
            or material_index >= len(self._gltf.materials)
        ):
            return Material(name=fallback_name)

        glb_material = GlbMaterialData(
            self._gltf.materials[material_index]
        )

        material = Material(
            name=(
                glb_material.name
                or fallback_name
            ),
        )

        if glb_material.pbr is not None:
            self._apply_pbr_material(
                material=material,
                pbr=glb_material.pbr,
            )

        if glb_material.emissive_factor is not None:
            material.emissive_factor = [
                float(glb_material.emissive_factor[0]),
                float(glb_material.emissive_factor[1]),
                float(glb_material.emissive_factor[2]),
            ]

        normal_texture = self._load_texture_from_info(
            glb_material.normal_texture
        )

        if normal_texture is not None:
            material.normal_texture = normal_texture

        emissive_texture = self._load_texture_from_info(
            glb_material.emissive_texture
        )

        if emissive_texture is not None:
            material.emissive_texture = emissive_texture

        occlusion_texture = self._load_texture_from_info(
            glb_material.occlusion_texture
        )

        if occlusion_texture is not None:
            material.occlusion_texture = occlusion_texture

        return material

    def _apply_pbr_material(
        self,
        material: Material,
        pbr: Any,
    ) -> None:
        base_color = getattr(
            pbr,
            "baseColorFactor",
            None,
        )

        metallic_factor = getattr(
            pbr,
            "metallicFactor",
            None,
        )

        roughness_factor = getattr(
            pbr,
            "roughnessFactor",
            None,
        )

        if base_color is not None:
            material.base_color = [
                float(base_color[0]),
                float(base_color[1]),
                float(base_color[2]),
                float(base_color[3]),
            ]

        if metallic_factor is not None:
            material.metallic_factor = float(metallic_factor)

        if roughness_factor is not None:
            material.roughness_factor = float(roughness_factor)

        base_color_texture = self._load_texture_from_info(
            getattr(
                pbr,
                "baseColorTexture",
                None,
            )
        )

        if base_color_texture is not None:
            material.base_color_texture = base_color_texture

        metallic_roughness_texture = self._load_texture_from_info(
            getattr(
                pbr,
                "metallicRoughnessTexture",
                None,
            )
        )

        if metallic_roughness_texture is not None:
            material.metallic_roughness_texture = (
                metallic_roughness_texture
            )

    # =================================== #
    # Textures / Images
    # =================================== #

    def _load_texture_from_info(
        self,
        texture_info: Any,
    ) -> Texture2D | None:
        if texture_info is None:
            return None

        texture_index = getattr(
            texture_info,
            "index",
            None,
        )

        if texture_index is None:
            return None

        return self._load_texture(texture_index)

    def _load_texture(
        self,
        texture_index: int,
    ) -> Texture2D | None:
        if (
            not self._gltf.textures
            or texture_index < 0
            or texture_index >= len(self._gltf.textures)
        ):
            return None

        cached_texture = self._texture_cache.get(texture_index)

        if cached_texture is not None:
            return cached_texture

        gltf_texture = self._gltf.textures[texture_index]

        image_index = getattr(
            gltf_texture,
            "source",
            None,
        )

        if image_index is None:
            return None

        sampler_key = self._get_sampler_cache_key(gltf_texture)

        texture = self._load_image_texture(
            image_index=image_index,
            sampler_key=sampler_key,
        )

        if texture is None:
            return None

        self._apply_sampler(
            texture=texture,
            gltf_texture=gltf_texture,
        )

        self._texture_cache[texture_index] = texture

        return texture

    def _load_image_texture(
        self,
        image_index: int,
        sampler_key: tuple[
            int | None,
            int | None,
            int | None,
            int | None,
        ],
    ) -> Texture2D | None:
        image_data = self._load_image_data(image_index)

        if image_data is None:
            return None

        image_bytes, extension = image_data

        image_hash = xxhash.xxh3_64_hexdigest(image_bytes)

        key = (
            image_hash,
            sampler_key[0],
            sampler_key[1],
            sampler_key[2],
            sampler_key[3],
        )

        cached_texture = self._image_texture_cache.get(key)

        if cached_texture is not None:
            return cached_texture


        texture = Texture2D.from_bytes(
            image_bytes,
            mipmap=True,
            wrap="repeat",
            min_filter="linear_mipmap_linear",
            mag_filter="linear",
        )

        self._image_texture_cache[key] = texture

        return texture

    def _load_image_data(
        self,
        image_index: int,
    ) -> tuple[bytes, str] | None:
        cached_data = self._image_bytes_cache.get(image_index)

        if cached_data is not None:
            return cached_data

        if (
            not self._gltf.images
            or image_index < 0
            or image_index >= len(self._gltf.images)
        ):
            return None

        image = self._gltf.images[image_index]

        image_bytes, extension = self._load_image_bytes(image=image)
        if image_bytes is None:
            return None

        image_data = (
            image_bytes,
            extension,
        )

        self._image_bytes_cache[image_index] = image_data

        return image_data

    def _get_sampler_cache_key(
        self,
        gltf_texture: Any,
    ) -> tuple[
        int | None,
        int | None,
        int | None,
        int | None,
    ]:
        sampler_index = getattr(
            gltf_texture,
            "sampler",
            None,
        )

        if (
            sampler_index is None
            or not self._gltf.samplers
            or sampler_index < 0
            or sampler_index >= len(self._gltf.samplers)
        ):
            return (
                None,
                None,
                None,
                None,
            )

        sampler = self._gltf.samplers[sampler_index]

        return (
            getattr(sampler, "minFilter", None),
            getattr(sampler, "magFilter", None),
            getattr(sampler, "wrapS", None),
            getattr(sampler, "wrapT", None),
        )

    def _apply_sampler(
        self,
        texture: Texture2D,
        gltf_texture: Any,
    ) -> None:
        sampler_index = getattr(
            gltf_texture,
            "sampler",
            None,
        )

        if (
            sampler_index is None
            or not self._gltf.samplers
            or sampler_index < 0
            or sampler_index >= len(self._gltf.samplers)
        ):
            return

        sampler = self._gltf.samplers[sampler_index]

        min_filter = self._sampler_min_filter_to_kivy(
            getattr(
                sampler,
                "minFilter",
                None,
            )
        )

        mag_filter = self._sampler_mag_filter_to_kivy(
            getattr(
                sampler,
                "magFilter",
                None,
            )
        )

        wrap_s = self._sampler_wrap_to_kivy(
            getattr(
                sampler,
                "wrapS",
                None,
            )
        )

        wrap_t = self._sampler_wrap_to_kivy(
            getattr(
                sampler,
                "wrapT",
                None,
            )
        )

        if min_filter is not None or mag_filter is not None:
            texture.set_filter(
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

        if wrap_s is not None and wrap_t is not None:
            if wrap_s == wrap_t:
                texture.set_wrap(
                    wrap_s,
                )

            else:
                texture.set_wrap(
                    wrap_s,
                )

        elif wrap_s is not None:
            texture.set_wrap(
                wrap_s,
            )

        elif wrap_t is not None:
            texture.set_wrap(
                wrap_t,
            )

    def _sampler_min_filter_to_kivy(
        self,
        value: int | None,
    ) -> TextureMinFilter | None:
        if value is None:
            return None

        return self._SAMPLER_MIN_FILTER_MAP.get(value)

    def _sampler_mag_filter_to_kivy(
        self,
        value: int | None,
    ) -> TextureMagFilter | None:
        if value is None:
            return None

        return self._SAMPLER_MAG_FILTER_MAP.get(value)

    def _sampler_wrap_to_kivy(
        self,
        value: int | None,
    ) -> TextureWrap | None:
        if value is None:
            return None

        return self._SAMPLER_WRAP_MAP.get(value)

    def _load_image_bytes(
        self,
        image: Any,
    ) -> tuple[bytes | None, str]:
        uri = getattr(
            image,
            "uri",
            None,
        )

        mime_type = getattr(
            image,
            "mimeType",
            None,
        )

        buffer_view_index = getattr(
            image,
            "bufferView",
            None,
        )

        if uri:
            if uri.startswith("data:"):
                header, encoded = uri.split(",", 1)

                mime_type = (
                    header.split(";", 1)[0].replace("data:", "")
                    or mime_type
                )

                return (
                    base64.b64decode(encoded),
                    self._extension_from_mime_type(mime_type),
                )

            if self._base_path is None:
                raise RuntimeError("GLB base path was not set.")

            image_path = (
                Path(uri)
                if os.path.isabs(uri)
                else self._base_path / uri
            )

            return (
                image_path.read_bytes(),
                image_path.suffix.lstrip(".") or "png",
            )

        if buffer_view_index is not None:
            return (
                self._read_buffer_view_bytes(buffer_view_index),
                self._extension_from_mime_type(mime_type),
            )

        return None, self._extension_from_mime_type(mime_type)

    def _read_buffer_view_bytes(
        self,
        buffer_view_index: int,
    ) -> bytes:
        if self._buffer_bytes is None:
            raise RuntimeError("GLB buffer bytes were not loaded.")

        view = self._gltf.bufferViews[buffer_view_index]

        byte_offset = view.byteOffset or 0
        byte_length = view.byteLength or 0

        return self._buffer_bytes[
            byte_offset : byte_offset + byte_length
        ]

    def _extension_from_mime_type(
        self,
        mime_type: str | None,
    ) -> str:
        if mime_type is None:
            return "png"

        return self._MIME_EXTENSION_MAP.get(
            mime_type,
            "png",
        )

    # =================================== #
    # Buffer Reading
    # =================================== #

    def _load_buffer_bytes(
        self,
        filename: Path,
    ) -> bytes:
        buffer_bytes = self._gltf.binary_blob()

        if buffer_bytes is not None:
            return buffer_bytes

        if not self._gltf.buffers:
            raise ValueError("No buffer found in GLB file.")

        uri = self._gltf.buffers[0].uri

        if uri and uri.startswith("data:"):
            encoded = uri.split(",", 1)[1]
            return base64.b64decode(encoded)

        if uri:
            bin_path = (
                Path(uri)
                if os.path.isabs(uri)
                else filename.parent / uri
            )

            with open(bin_path, "rb") as file:
                return file.read()

        raise ValueError("No binary buffer found in GLB file.")

    def _read_accessor(
        self,
        accessor_index: int | None,
    ) -> np.ndarray | None:
        if accessor_index is None:
            return None

        if self._buffer_bytes is None:
            raise RuntimeError("GLB buffer bytes were not loaded.")

        buffer_bytes = self._buffer_bytes
        accessor = self._gltf.accessors[accessor_index]

        if accessor.bufferView is None:
            return None

        view = self._gltf.bufferViews[accessor.bufferView]

        view_offset = view.byteOffset or 0
        accessor_offset = accessor.byteOffset or 0
        stride = view.byteStride or 0
        count = accessor.count

        dtype = self._DTYPE_MAP[accessor.componentType]

        component_count = self._COMPONENT_COUNT_MAP.get(
            accessor.type,
            1,
        )

        dtype_info = np.dtype(dtype)
        element_size = dtype_info.itemsize * component_count
        start = view_offset + accessor_offset

        if stride and stride != element_size:
            return np.ndarray(
                shape=(count, component_count),
                dtype=dtype,
                buffer=buffer_bytes,
                offset=start,
                strides=(
                    stride,
                    dtype_info.itemsize,
                ),
            )

        array = np.frombuffer(
            buffer_bytes,
            dtype=dtype,
            count=count * component_count,
            offset=start,
        )

        return array.reshape((count, component_count))

    # =================================== #
    # Geometry
    # =================================== #
    def _process_primitive_geometry(
        self,
        primitive: GlbPrimitiveData,
    ) -> Geometry | None:
        if primitive.position_index is None:
            return None

        mode = self._GLTF_MODE_MAP.get(
            primitive.mode,
            "triangles",
        )

        positions = self._read_accessor(
            primitive.position_index,
        )

        if positions is None:
            return None

        positions = positions.astype(
            np.float32,
            copy=False,
        )

        vertex_count = positions.shape[0]

        # =================================== #
        # Indices
        # =================================== #

        if primitive.indices_index is not None:
            indices = self._read_accessor(
                primitive.indices_index,
            )

            if indices is None:
                return None

            final_indices = indices.reshape(-1).astype(
                np.int64,
                copy=False,
            )

        else:
            final_indices = np.arange(
                vertex_count,
                dtype=np.int64,
            )

        # =================================== #
        # Normals
        # =================================== #

        normals = self._read_accessor(
            primitive.normal_index,
        )

        if normals is None or normals.shape[1] < 3:
            normals = np.zeros_like(
                positions[:, :3],
                dtype=np.float32,
            )

        else:
            normals = normals[:, :3].astype(
                np.float32,
                copy=False,
            )

        # =================================== #
        # UVs
        # =================================== #

        uvs = self._read_accessor(
            primitive.uv_index,
        )

        if uvs is None or uvs.shape[1] < 2:
            uvs = np.zeros(
                (vertex_count, 2),
                dtype=np.float32,
            )

        else:
            uvs = uvs[:, :2].astype(
                np.float32,
                copy=False,
            )

            if self.flip_v:
                uvs = uvs.copy()

        if self.flip_v:
            uvs[:, 1] = 1.0 - uvs[:, 1]

        # =================================== #
        # Dynamic Vertex Format
        # =================================== #

        columns: list[np.ndarray] = [
            positions[:, :3],
            normals,
            uvs,
        ]

        fmt: list[tuple[bytes, int, str]] = [
            (b"v_pos", 3, "float"),
            (b"v_normal", 3, "float"),
            (b"v_uv", 2, "float"),
        ]

        # =================================== #
        # Tangents
        # =================================== #

        tangents = self._read_accessor(
            primitive.tangent_index,
        )

        has_tangents = (
            tangents is not None
            and tangents.shape[1] >= 4
        )

        if has_tangents:
            assert tangents is not None

            tangents = tangents[:, :4].astype(
                np.float32,
                copy=False,
            )

            columns.append(tangents)
            fmt.append((b"v_tangent", 4, "float"))

        # =================================== #
        # Skinning: JOINTS_0 / WEIGHTS_0
        # =================================== #

        joints = self._read_accessor(
            primitive.joints_index,
        )

        weights = self._read_accessor(
            primitive.weights_index,
        )

        has_valid_joints = (
            joints is not None
            and joints.shape[1] >= 4
        )

        has_valid_weights = (
            weights is not None
            and weights.shape[1] >= 4
        )

        has_skin = has_valid_joints and has_valid_weights

        if has_skin:
            assert joints is not None
            assert weights is not None

            joints = joints[:, :4].astype(
                np.float32,
                copy=False,
            )

            weights = weights[:, :4].astype(
                np.float32,
                copy=False,
            )

            columns.append(joints)
            columns.append(weights)

            fmt.append((b"v_joints", 4, "float"))
            fmt.append((b"v_weights", 4, "float"))

        packed_vertices = np.column_stack(
            columns,
        ).reshape(-1)

        morph_targets: list[MorphTarget] = []
        for raw_target in primitive.targets:
            position_index = getattr(raw_target, "POSITION", None)
            normal_index = getattr(raw_target, "NORMAL", None)
            tangent_index = getattr(raw_target, "TANGENT", None)

            morph_positions = self._read_accessor(position_index)
            morph_normals = self._read_accessor(normal_index)
            morph_tangents = self._read_accessor(tangent_index)

            if morph_positions is not None:
                morph_positions = morph_positions[:, :3].astype(
                    np.float32,
                    copy=False,
                )

            if morph_normals is not None:
                morph_normals = morph_normals[:, :3].astype(
                    np.float32,
                    copy=False,
                )

            if morph_tangents is not None:
                morph_tangents = morph_tangents[:, :3].astype(
                    np.float32,
                    copy=False,
                )

            morph_targets.append(
                MorphTarget(
                    positions=morph_positions,
                    normals=morph_normals,
                    tangents=morph_tangents,
                )
            )

        # =================================== #
        # Winding
        # =================================== #

        if self.flip_winding and len(final_indices) % 3 == 0:
            final_indices = final_indices.reshape(-1, 3)
            final_indices[:, [1, 2]] = final_indices[:, [2, 1]]
            final_indices = final_indices.reshape(-1)

        final_indices = self._ensure_uint16_indices(
            final_indices,
        )

        bounds = GeometryBounds.from_positions(
            positions,
        )

        return Geometry(
            fmt=fmt,
            vertices=packed_vertices,
            indices=final_indices,
            bounds=bounds,
            mode=mode,
            has_tangents=has_tangents,
            has_skin=has_skin,
            morph_targets=tuple(morph_targets),
        )


    def _ensure_uint16_indices(
        self,
        indices: np.ndarray,
    ) -> np.ndarray:
        if indices.size == 0:
            return indices.astype(
                np.uint16,
                copy=False,
            )

        total = int(indices.max())

        if total > 65535:
            raise OverflowError(
                "Indices exceed 65535 in a single primitive. "
                "Split the primitive before loading it."
            )

        return indices.astype(
            np.uint16,
            copy=False,
        )
