# kivyfn/three/lights/template.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kivyfn.three.render.shader import Shader


from kivyfn.three.lights.sources.directional import DirectionalLight
from kivyfn.three.lights.sources.spot import SpotLight
from kivyfn.three.lights.sources.point import PointLight


# =================================== #
# Runtime Config
# =================================== #
@dataclass(slots=True, frozen=True)
class ShadowViewConfig:
    projection_type: Literal["perspective", "orthographic"]

    near: float
    far: float

    ortho_size: float
    fov: float


@dataclass(slots=True, frozen=True)
class ShadowConfig:
    shader: Shader

    view: ShadowViewConfig

    texture_uniform: str
    view_uniform: str
    projection_uniform: str

    enabled: bool
    resolution: int

    caster_tags: frozenset[str]
    receiver_tags: frozenset[str]

    bias: float
    normal_bias: float


@dataclass(slots=True, frozen=True)
class LightConfig:

    base_name: str
    affected_tags: frozenset[str]
    shadow: ShadowConfig | None = None


# =================================== #
# Shadow View Template
# =================================== #
@dataclass(slots=True, frozen=True)
class ShadowViewTemplate:
    projection_type: Literal["perspective", "orthographic"] = "orthographic"

    near: float = 1.0
    far: float = 1000.0

    ortho_size: float = 256.0
    fov: float = 45.0

    def create(self) -> ShadowViewConfig:
        return ShadowViewConfig(
            projection_type=self.projection_type,
            near=self.near,
            far=self.far,
            ortho_size=self.ortho_size,
            fov=self.fov,
        )


# =================================== #
# Shadow Template
# =================================== #
@dataclass(slots=True, frozen=True)
class ShadowTemplate:
    shader: Shader

    enabled: bool = True
    resolution: int = 2048

    caster_tags: set[str] = field(default_factory=lambda: {"shadow_caster"})
    receiver_tags: set[str] = field(default_factory=lambda: {"shadow_receiver"})

    view_template: ShadowViewTemplate = field(default_factory=ShadowViewTemplate)

    texture_uniform: str = "shadow_texture"
    view_uniform: str = "shadow_view_mat"
    projection_uniform: str = "shadow_projection_mat"

    bias: float = 0.005
    normal_bias: float = 0.05

    def create(self) -> ShadowConfig:
        return ShadowConfig(
            shader=self.shader,
            enabled=self.enabled,
            resolution=self.resolution,
            caster_tags=frozenset(self.caster_tags),
            receiver_tags=frozenset(self.receiver_tags),
            view=self.view_template.create(),
            texture_uniform=self.texture_uniform,
            view_uniform=self.view_uniform,
            projection_uniform=self.projection_uniform,
            bias=self.bias,
            normal_bias=self.normal_bias,
        )


# =================================== #
# Light Template
# =================================== #
@dataclass(slots=True, frozen=True)
class LightTemplate:
    affected_tags: set[str] = field(default_factory=lambda: {"lit"})
    shadow_template: ShadowTemplate | None = None

    def _config(
        self,
        base_name: str,
    ) -> LightConfig:
        return LightConfig(
            base_name=base_name,
            affected_tags=frozenset(self.affected_tags),
            shadow=(
                self.shadow_template.create()
                if self.shadow_template is not None
                else None
            ),
        )

    def directional(
        self,
        *,
        base_name: str,
        **kwargs,
    ) -> DirectionalLight:

        return DirectionalLight(
            config=self._config(base_name),
            **kwargs,
        )

    def spot(
        self,
        *,
        base_name: str,
        **kwargs,
    ) -> SpotLight:

        return SpotLight(
            config=self._config(base_name),
            **kwargs,
        )

    def point(
        self,
        *,
        base_name: str,
        **kwargs,
    ) -> PointLight:

        return PointLight(
            config=self._config(base_name),
            **kwargs,
        )






