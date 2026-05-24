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


from kivyfn.three.utils.texture import create_texture


WHITE_TEXTURE = create_texture(
    (255, 255, 255, 255),
)

FLAT_NORMAL_TEXTURE = create_texture(
    (128, 128, 255, 255),
)


class Material(EventDispatcher):

    name = StringProperty("")

    # =================================== #
    # PBR Core
    # =================================== #

    metallic_factor: float = NumericProperty(0.0)

    roughness_factor: float = NumericProperty(1.0)

    emissive_factor: list[float] = ListProperty([0.0, 0.0, 0.0])

    base_color: list[float] = ListProperty(
        [1.0, 1.0, 1.0, 1.0],
    )

    base_texture: Texture = ObjectProperty(
        WHITE_TEXTURE,
    )

    normal_texture: Texture = ObjectProperty(
        FLAT_NORMAL_TEXTURE,
    )

    emissive_texture: Texture = ObjectProperty(
        WHITE_TEXTURE,
    )

    metallic_roughness_texture: Texture = ObjectProperty(
        WHITE_TEXTURE,
    )

    occlusion_texture: Texture = ObjectProperty(
        WHITE_TEXTURE,
    )

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
        metallic_roughness_texture: Texture | None = None,
        occlusion_texture: Texture | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.name = name

        if metallic_factor is not None:
            self.metallic_factor = metallic_factor

        if roughness_factor is not None:
            self.roughness_factor = roughness_factor

        if emissive_factor is not None:
            self.emissive_factor = emissive_factor

        if base_color is not None:
            self.base_color = base_color

        if base_texture is not None:
            self.base_texture = base_texture

        if normal_texture is not None:
            self.normal_texture = normal_texture

        if emissive_texture is not None:
            self.emissive_texture = emissive_texture

        if metallic_roughness_texture is not None:
            self.metallic_roughness_texture = metallic_roughness_texture

        if occlusion_texture is not None:
            self.occlusion_texture = occlusion_texture

        self.bind(
            metallic_factor=self.sync_uniforms,
            roughness_factor=self.sync_uniforms,
            emissive_factor=self.sync_uniforms,
            base_color=self.sync_uniforms,
            base_texture=self.sync_uniforms,
            normal_texture=self.sync_uniforms,
            emissive_texture=self.sync_uniforms,
            metallic_roughness_texture=self.sync_uniforms,
            occlusion_texture=self.sync_uniforms,
        )

        self.sync_uniforms()

    def sync_uniforms(self, *_):
        self.set_uniform(
            "metallic_factor",
            float(self.metallic_factor),
        )

        self.set_uniform(
            "roughness_factor",
            float(self.roughness_factor),
        )

        self.set_uniform(
            "emissive_factor",
            list(self.emissive_factor),
        )

        self.set_uniform(
            "base_color",
            list(self.base_color),
        )

        self.set_uniform(
            "base_texture",
            self.base_texture,
        )

        self.set_uniform(
            "normal_texture",
            self.normal_texture,
        )

        self.set_uniform(
            "emissive_texture",
            self.emissive_texture,
        )

        self.set_uniform(
            "metallic_roughness_texture",
            self.metallic_roughness_texture,
        )

        self.set_uniform(
            "occlusion_texture",
            self.occlusion_texture,
        )

    def set_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.uniforms[name] = value

    def remove_uniform(
        self,
        name: str,
    ) -> None:
        self.uniforms.pop(name, None)

    def clear_uniforms(self) -> None:
        self.uniforms.clear()
