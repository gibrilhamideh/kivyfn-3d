# kivyfn/three/assets/material.py

from __future__ import annotations

from pprint import pformat
from typing import Any

from kivy.event import EventDispatcher
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)

from kivyfn.three.graphics.gl.texture import Texture2D


MATERIAL_UNIFORM_FIELDS = {
    "metallic_factor",
    "roughness_factor",
    "emissive_factor",
    "base_color",
    "use_base_color_texture",
    "use_normal_texture",
    "use_emissive_texture",
    "use_occlusion_texture",
    "use_metallic_roughness_texture",
    "use_roughness_texture",
    "use_metallic_texture",
    "use_specular_texture",
    "use_displacement_texture",
}


MATERIAL_TEXTURE_FIELDS = {
    "base_color_texture",
    "normal_texture",
    "emissive_texture",
    "occlusion_texture",
    "metallic_roughness_texture",
    "roughness_texture",
    "metallic_texture",
    "specular_texture",
    "displacement_texture",
}


MATERIAL_FIELDS = MATERIAL_UNIFORM_FIELDS | MATERIAL_TEXTURE_FIELDS


class Material(EventDispatcher):
    """
    Standard PBR-ish material data.

    Material separates shader values from texture resources:

        material.uniforms
            Final scalar/vector/bool values sent to the shader.
            Texture objects are never stored here.

        material.textures
            Texture resources by sampler name.
            Values may be Texture2D or None.

        material.custom
            User-defined extra shader uniforms.
            Mutate through set_custom/remove_custom/clear_custom.

    A texture value of None means the texture is absent. Built-in shaders should
    guard optional texture sampling with the matching use_*_texture uniform.
    """

    name: str = StringProperty("")

    # =================================== #
    # PBR Core Factors
    # =================================== #

    metallic_factor: float = NumericProperty(0.0)

    roughness_factor: float = NumericProperty(1.0)

    emissive_factor: list[float] = ListProperty(
        [0.0, 0.0, 0.0],
    )

    base_color: list[float] = ListProperty(
        [0.65, 0.65, 0.65, 1.0],
    )

    # =================================== #
    # Core Engine & glTF Packed Maps
    # =================================== #

    base_color_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    normal_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    emissive_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    occlusion_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    metallic_roughness_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    # =================================== #
    # Standard / Loose Maps
    # =================================== #

    roughness_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    metallic_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    specular_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    displacement_texture: Texture2D | None = ObjectProperty(
        None,
        allownone=True,
    )

    __events__ = (
        "on_dirty",
    )

    def __init__(
        self,
        name: str = "",
        metallic_factor: float | None = None,
        roughness_factor: float | None = None,
        emissive_factor: list[float] | None = None,
        base_color: list[float] | None = None,
        base_color_texture: Texture2D | None = None,
        normal_texture: Texture2D | None = None,
        emissive_texture: Texture2D | None = None,
        occlusion_texture: Texture2D | None = None,
        metallic_roughness_texture: Texture2D | None = None,
        roughness_texture: Texture2D | None = None,
        metallic_texture: Texture2D | None = None,
        specular_texture: Texture2D | None = None,
        displacement_texture: Texture2D | None = None,
        custom: dict[str, Any] | None = None,
        **custom_values: Any,
    ) -> None:
        super().__init__()

        self._custom: dict[str, Any] = {}

        self.name = name

        # =================================== #
        # Factors
        # =================================== #

        if metallic_factor is not None:
            self.metallic_factor = metallic_factor

        if roughness_factor is not None:
            self.roughness_factor = roughness_factor

        if emissive_factor is not None:
            self.emissive_factor = emissive_factor

        if base_color is not None:
            self.base_color = base_color

        # =================================== #
        # Core / Packed Textures
        # =================================== #

        self.base_color_texture = base_color_texture
        self.normal_texture = normal_texture
        self.emissive_texture = emissive_texture
        self.occlusion_texture = occlusion_texture
        self.metallic_roughness_texture = metallic_roughness_texture

        # =================================== #
        # Loose Textures
        # =================================== #

        self.roughness_texture = roughness_texture
        self.metallic_texture = metallic_texture
        self.specular_texture = specular_texture
        self.displacement_texture = displacement_texture

        if custom is not None:
            for key, value in custom.items():
                self.set_custom(
                    key,
                    value,
                )

        for key, value in custom_values.items():
            self.set_custom(
                key,
                value,
            )

        self.bind(
            metallic_factor=self._mark_dirty,
            roughness_factor=self._mark_dirty,
            emissive_factor=self._mark_dirty,
            base_color=self._mark_dirty,
            base_color_texture=self._mark_dirty,
            normal_texture=self._mark_dirty,
            emissive_texture=self._mark_dirty,
            occlusion_texture=self._mark_dirty,
            metallic_roughness_texture=self._mark_dirty,
            roughness_texture=self._mark_dirty,
            metallic_texture=self._mark_dirty,
            specular_texture=self._mark_dirty,
            displacement_texture=self._mark_dirty,
        )

    def __repr__(
        self,
    ) -> str:
        return (
            "Material("
            f"name={self.name!r}, "
            f"uniforms={pformat(self.uniforms)}, "
            f"textures={pformat(self.textures)}"
            ")"
        )

    # =================================== #
    # Uniforms
    # =================================== #

    @property
    def uniforms(
        self,
    ) -> dict[str, Any]:
        """
        Final scalar/vector/bool shader uniforms.

        Sampler uniforms are not set here. Sampler uniforms are assigned to
        texture slots by the texture binding layer.
        """
        return {
            "metallic_factor": float(self.metallic_factor),
            "roughness_factor": float(self.roughness_factor),
            "emissive_factor": list(self.emissive_factor),
            "base_color": list(self.base_color),

            "use_base_color_texture": int(self.base_color_texture is not None),
            "use_normal_texture": int(self.normal_texture is not None),
            "use_emissive_texture": int(self.emissive_texture is not None),
            "use_occlusion_texture": int(self.occlusion_texture is not None),
            "use_metallic_roughness_texture": int(
                self.metallic_roughness_texture is not None
            ),
            "use_roughness_texture": int(self.roughness_texture is not None),
            "use_metallic_texture": int(self.metallic_texture is not None),
            "use_specular_texture": int(self.specular_texture is not None),
            "use_displacement_texture": int(self.displacement_texture is not None),

            **self._custom,
        }

    # =================================== #
    # Custom Uniforms
    # =================================== #

    @property
    def custom(
        self,
    ) -> dict[str, Any]:
        return self._custom.copy()

    def set_custom(
        self,
        name: str,
        value: Any,
    ) -> None:
        if name in MATERIAL_UNIFORM_FIELDS:
            raise KeyError(
                f"{name!r} is a built-in Material uniform. "
                "Set the matching Material property directly instead."
            )

        if name in MATERIAL_TEXTURE_FIELDS:
            raise KeyError(
                f"{name!r} is a Material texture field. "
                "Set the matching texture property directly instead."
            )

        self._custom[name] = value
        self._mark_dirty()

    def remove_custom(
        self,
        name: str,
    ) -> None:
        self._custom.pop(
            name,
            None,
        )

        self._mark_dirty()

    def clear_custom(
        self,
    ) -> None:
        self._custom.clear()
        self._mark_dirty()

    # =================================== #
    # Textures
    # =================================== #

    @property
    def textures(
        self,
    ) -> dict[str, Texture2D | None]:
        """
        Texture resources by sampler name.

        None means the material does not have that texture.
        """
        return {
            "base_color_texture": self.base_color_texture,
            "normal_texture": self.normal_texture,
            "emissive_texture": self.emissive_texture,
            "occlusion_texture": self.occlusion_texture,
            "metallic_roughness_texture": self.metallic_roughness_texture,
            "roughness_texture": self.roughness_texture,
            "metallic_texture": self.metallic_texture,
            "specular_texture": self.specular_texture,
            "displacement_texture": self.displacement_texture,
        }

    # =================================== #
    # Copy
    # =================================== #

    def copy(
        self,
        **overrides: Any,
    ) -> Material:
        custom = dict(self._custom)

        custom.update(
            overrides.pop(
                "custom",
                {},
            )
        )

        # Temporary migration convenience.
        # Remove this once old base_texture usage is gone.
        if "base_texture" in overrides:
            overrides["base_color_texture"] = overrides.pop("base_texture")

        return Material(
            name=overrides.pop(
                "name",
                self.name,
            ),
            metallic_factor=overrides.pop(
                "metallic_factor",
                self.metallic_factor,
            ),
            roughness_factor=overrides.pop(
                "roughness_factor",
                self.roughness_factor,
            ),
            emissive_factor=overrides.pop(
                "emissive_factor",
                list(self.emissive_factor),
            ),
            base_color=overrides.pop(
                "base_color",
                list(self.base_color),
            ),
            base_color_texture=overrides.pop(
                "base_color_texture",
                self.base_color_texture,
            ),
            normal_texture=overrides.pop(
                "normal_texture",
                self.normal_texture,
            ),
            emissive_texture=overrides.pop(
                "emissive_texture",
                self.emissive_texture,
            ),
            occlusion_texture=overrides.pop(
                "occlusion_texture",
                self.occlusion_texture,
            ),
            metallic_roughness_texture=overrides.pop(
                "metallic_roughness_texture",
                self.metallic_roughness_texture,
            ),
            roughness_texture=overrides.pop(
                "roughness_texture",
                self.roughness_texture,
            ),
            metallic_texture=overrides.pop(
                "metallic_texture",
                self.metallic_texture,
            ),
            specular_texture=overrides.pop(
                "specular_texture",
                self.specular_texture,
            ),
            displacement_texture=overrides.pop(
                "displacement_texture",
                self.displacement_texture,
            ),
            custom=custom,
            **overrides,
        )

    # =================================== #
    # Dirty Flags
    # =================================== #
    def _mark_dirty(
        self,
        *_,
    ) -> None:
            self.dispatch(
                "on_dirty",
            )

    def on_dirty(
        self,
    ) -> None:
        pass
