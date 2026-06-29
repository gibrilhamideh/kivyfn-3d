# kivyfn/three/parsers/glb/parser/data.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    def skin_index(self) -> int | None:
        return getattr(self.raw, "skin", None)

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
class GlbMeshData:
    raw: Any

    @property
    def name(self) -> str | None:
        return getattr(self.raw, "name", None)

    @property
    def primitives(self) -> list[Any]:
        return list(getattr(self.raw, "primitives", None) or [])

    @property
    def weights(self) -> tuple[float, ...]:
        return tuple(
            float(value)
            for value in list(getattr(self.raw, "weights", None) or [])
        )

@dataclass(slots=True)
class GlbMorphTargetData:
    raw: Any

    @property
    def position_index(self) -> int | None:
        return getattr(self.raw, "POSITION", None)

    @property
    def normal_index(self) -> int | None:
        return getattr(self.raw, "NORMAL", None)

    @property
    def tangent_index(self) -> int | None:
        return getattr(self.raw, "TANGENT", None)


@dataclass(slots=True)
class GlbPrimitiveData:
    raw: Any

    @property
    def attributes(self) -> Any:
        return self.raw.attributes

    @property
    def color_index(self) -> int | None:
        return getattr(self.attributes, "COLOR_0", None)

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
class GlbSkinData:
    raw: Any

    @property
    def name(self) -> str | None:
        return getattr(self.raw, "name", None)

    @property
    def joints(self) -> list[int]:
        return list(getattr(self.raw, "joints", None) or [])

    @property
    def inverse_bind_matrices_index(self) -> int | None:
        return getattr(self.raw, "inverseBindMatrices", None)


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
class GlbPbrData:
    raw: Any

    @property
    def base_color_factor(self) -> list[float] | None:
        return getattr(self.raw, "baseColorFactor", None)

    @property
    def metallic_factor(self) -> float | None:
        return getattr(self.raw, "metallicFactor", None)

    @property
    def roughness_factor(self) -> float | None:
        return getattr(self.raw, "roughnessFactor", None)

    @property
    def base_color_texture(self) -> Any:
        return getattr(self.raw, "baseColorTexture", None)

    @property
    def metallic_roughness_texture(self) -> Any:
        return getattr(self.raw, "metallicRoughnessTexture", None)

@dataclass(slots=True)
class GlbMaterialExtensionData:
    raw: Any

    @property
    def extensions(self) -> dict[str, Any]:
        return dict(getattr(self.raw, "extensions", None) or {})

    @property
    def specular_glossiness(self) -> dict[str, Any] | None:
        return self.extensions.get(
            "KHR_materials_pbrSpecularGlossiness",
            None,
        )

    @property
    def diffuse_factor(self) -> list[float] | None:
        data = self.specular_glossiness

        if data is None:
            return None

        return data.get(
            "diffuseFactor",
            None,
        )

    @property
    def diffuse_texture(self) -> Any:
        data = self.specular_glossiness

        if data is None:
            return None

        return data.get(
            "diffuseTexture",
            None,
        )

    @property
    def glossiness_factor(self) -> float | None:
        data = self.specular_glossiness

        if data is None:
            return None

        return data.get(
            "glossinessFactor",
            None,
        )


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
        return getattr(self.raw, "target", None)

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


@dataclass(slots=True)
class GlbTextureData:
    raw: Any

    @property
    def source_index(self) -> int | None:
        return getattr(self.raw, "source", None)

    @property
    def sampler_index(self) -> int | None:
        return getattr(self.raw, "sampler", None)


@dataclass(slots=True)
class GlbImageData:
    raw: Any

    @property
    def uri(self) -> str | None:
        return getattr(self.raw, "uri", None)

    @property
    def buffer_view_index(self) -> int | None:
        return getattr(self.raw, "bufferView", None)


@dataclass(slots=True)
class GlbSamplerData:
    raw: Any

    @property
    def min_filter(self) -> int | None:
        return getattr(self.raw, "minFilter", None)

    @property
    def mag_filter(self) -> int | None:
        return getattr(self.raw, "magFilter", None)

    @property
    def wrap_s(self) -> int | None:
        return getattr(self.raw, "wrapS", None)

    @property
    def wrap_t(self) -> int | None:
        return getattr(self.raw, "wrapT", None)



