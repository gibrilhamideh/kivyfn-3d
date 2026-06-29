# kivyfn/three/parsers/glb/parser/materials.py

from __future__ import annotations

from kivyfn.three.assets.material import Material
from kivyfn.three.parsers.glb.parser.context import GlbContext
from kivyfn.three.parsers.glb.parser.textures import GlbTextures
from kivyfn.three.parsers.glb.parser.data import (
    GlbMaterialData,
    GlbMaterialExtensionData,
    GlbPbrData,
    GlbPrimitiveData,
)


class GlbMaterials:
    def __init__(
        self,
        context: GlbContext,
        textures: GlbTextures,
    ) -> None:
        self.context = context
        self.textures = textures

    def load(
        self,
        *,
        primitive: GlbPrimitiveData,
        fallback_name: str,
    ) -> Material:
        index = primitive.material_index
        gltf = self.context.gltf

        if (
            index is None
            or not gltf.materials
            or index < 0
            or index >= len(gltf.materials)
        ):
            return Material(
                name=fallback_name,
            )

        data = GlbMaterialData(
            gltf.materials[index],
        )

        material = Material(
            name=(
                data.name
                or fallback_name
            ),
        )

        if data.pbr is not None:
            self.pbr(
                material=material,
                data=GlbPbrData(data.pbr),
            )

        self.extension(
            material=material,
            data=GlbMaterialExtensionData(data.raw),
        )

        self.emissive(
            material=material,
            data=data,
        )

        self.textures_to(
            material=material,
            data=data,
        )

        return material

    def pbr(
        self,
        *,
        material: Material,
        data: GlbPbrData,
    ) -> None:
        if data.base_color_factor is not None:
            material.base_color = [
                float(data.base_color_factor[0]),
                float(data.base_color_factor[1]),
                float(data.base_color_factor[2]),
                float(data.base_color_factor[3]),
            ]

        if data.metallic_factor is not None:
            material.metallic_factor = float(
                data.metallic_factor,
            )

        if data.roughness_factor is not None:
            material.roughness_factor = float(
                data.roughness_factor,
            )

        base_color_texture = self.textures.resolve(
            data.base_color_texture,
        )

        if base_color_texture is not None:
            material.base_color_texture = base_color_texture

        metallic_roughness_texture = self.textures.resolve(
            data.metallic_roughness_texture,
        )

        if metallic_roughness_texture is not None:
            material.metallic_roughness_texture = (
                metallic_roughness_texture
            )

    def extension(
        self,
        *,
        material: Material,
        data: GlbMaterialExtensionData,
    ) -> None:
        if data.diffuse_factor is not None:
            material.base_color = [
                float(data.diffuse_factor[0]),
                float(data.diffuse_factor[1]),
                float(data.diffuse_factor[2]),
                float(data.diffuse_factor[3]),
            ]

        diffuse_texture = self.textures.resolve(
            data.diffuse_texture,
        )

        if diffuse_texture is not None:
            material.base_color_texture = diffuse_texture

        if data.glossiness_factor is not None:
            material.roughness_factor = max(
                0.0,
                min(
                    1.0,
                    1.0 - float(data.glossiness_factor),
                ),
            )

    def emissive(
        self,
        *,
        material: Material,
        data: GlbMaterialData,
    ) -> None:
        if data.emissive_factor is None:
            return

        material.emissive_factor = [
            float(data.emissive_factor[0]),
            float(data.emissive_factor[1]),
            float(data.emissive_factor[2]),
        ]

    def textures_to(
        self,
        *,
        material: Material,
        data: GlbMaterialData,
    ) -> None:
        normal_texture = self.textures.resolve(
            data.normal_texture,
        )

        if normal_texture is not None:
            material.normal_texture = normal_texture

        emissive_texture = self.textures.resolve(
            data.emissive_texture,
        )

        if emissive_texture is not None:
            material.emissive_texture = emissive_texture

        occlusion_texture = self.textures.resolve(
            data.occlusion_texture,
        )

        if occlusion_texture is not None:
            material.occlusion_texture = occlusion_texture

