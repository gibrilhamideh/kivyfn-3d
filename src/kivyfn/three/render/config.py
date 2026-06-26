# kivyfn/three/render/config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderInstanceConfig:
    use_material: bool = True
    use_textures: bool = True
    use_render_id: bool = False


TEXTURE_SLOTS: dict[str, int] = {
    "base_color_texture": 1,
    "normal_texture": 2,
    "emissive_texture": 3,
    "metallic_roughness_texture": 4,
    "occlusion_texture": 5,
    "roughness_texture": 6,
    "metallic_texture": 7,
    "specular_texture": 8,
    "displacement_texture": 9,
}
