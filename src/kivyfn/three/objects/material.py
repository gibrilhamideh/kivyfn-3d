# kivyfn/three/render/material.py

from __future__ import annotations

from typing import Any

from kivy.event import EventDispatcher
from kivy.graphics.texture import Texture
from kivy.properties import (
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)


class Material(EventDispatcher):

    name = StringProperty("")

    # =================================== #
    # PBR Core Factors
    # =================================== #

    metallic_factor: float = NumericProperty(0.0)

    roughness_factor: float = NumericProperty(1.0)

    emissive_factor: list[float] = ListProperty([0.0, 0.0, 0.0])

    base_color: list[float] = ListProperty(
        [1.0, 1.0, 1.0, 1.0],
    )

    # =================================== #
    # Core Engine & glTF Packed Maps
    # =================================== #

    base_texture: Texture | None = ObjectProperty(None)

    normal_texture: Texture | None = ObjectProperty(None)

    emissive_texture: Texture | None = ObjectProperty(None)

    occlusion_texture: Texture | None = ObjectProperty(None)

    metallic_roughness_texture: Texture | None = ObjectProperty(None)

    # =================================== #
    # Standard Maps
    # =================================== #

    roughness_texture: Texture | None = ObjectProperty(None)

    metallic_texture: Texture | None = ObjectProperty(None)

    specular_texture: Texture | None = ObjectProperty(None)

    displacement_texture: Texture | None = ObjectProperty(None)

    # =================================== #
    # Custom Uniforms
    # =================================== #

    uniforms = DictProperty({})

    def __repr__(self) -> str:
        return (
            f"Material("
            f"name={self.name!r}"
            f")"
        )

    def __init__(
        self,
        name: str = "",
        metallic_factor: float | None = None,
        roughness_factor: float | None = None,
        emissive_factor: list[float] | None = None,
        base_color: list[float] | None = None,
        base_texture: Texture | None = None,
        normal_texture: Texture | None = None,
        emissive_texture: Texture | None = None,
        occlusion_texture: Texture | None = None,
        metallic_roughness_texture: Texture | None = None,
        roughness_texture: Texture | None = None,
        metallic_texture: Texture | None = None,
        specular_texture: Texture | None = None,
        displacement_texture: Texture | None = None,
        **kwargs,
    ):
        super().__init__()

        self.name = name
        self.uniforms = kwargs

        # Factors
        if metallic_factor is not None:
            self.metallic_factor = metallic_factor

        if roughness_factor is not None:
            self.roughness_factor = roughness_factor

        if emissive_factor is not None:
            self.emissive_factor = emissive_factor

        if base_color is not None:
            self.base_color = base_color

        # Core / Packed Textures
        self.base_texture = base_texture
        self.normal_texture = normal_texture
        self.emissive_texture = emissive_texture
        self.occlusion_texture = occlusion_texture
        self.metallic_roughness_texture = metallic_roughness_texture

        # Loose Textures
        self.roughness_texture = roughness_texture
        self.metallic_texture = metallic_texture
        self.specular_texture = specular_texture
        self.displacement_texture = displacement_texture

        # Bind reactive properties to sync with uniforms dict
        self.bind(
            metallic_factor=self.sync_uniforms,
            roughness_factor=self.sync_uniforms,
            emissive_factor=self.sync_uniforms,
            base_color=self.sync_uniforms,
            base_texture=self.sync_uniforms,
            normal_texture=self.sync_uniforms,
            emissive_texture=self.sync_uniforms,
            occlusion_texture=self.sync_uniforms,
            metallic_roughness_texture=self.sync_uniforms,
            roughness_texture=self.sync_uniforms,
            metallic_texture=self.sync_uniforms,
            specular_texture=self.sync_uniforms,
            displacement_texture=self.sync_uniforms,
        )

        self.sync_uniforms()

    def sync_uniforms(self, *_):
        self.set_uniform("metallic_factor", float(self.metallic_factor))
        self.set_uniform("roughness_factor", float(self.roughness_factor))
        self.set_uniform("emissive_factor", list(self.emissive_factor))
        self.set_uniform("base_color", list(self.base_color))

        # Core / Packed Textures
        self.set_uniform("base_texture", self.base_texture)
        self.set_uniform("normal_texture", self.normal_texture)
        self.set_uniform("emissive_texture", self.emissive_texture)
        self.set_uniform("occlusion_texture", self.occlusion_texture)
        self.set_uniform("metallic_roughness_texture", self.metallic_roughness_texture)

        # Loose Textures
        self.set_uniform("roughness_texture", self.roughness_texture)
        self.set_uniform("metallic_texture", self.metallic_texture)
        self.set_uniform("specular_texture", self.specular_texture)
        self.set_uniform("displacement_texture", self.displacement_texture)

    def set_uniform(self, name: str, value: Any) -> None:
        self.uniforms[name] = value


