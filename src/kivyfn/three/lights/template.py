# kivyfn/three/lights/template.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, Literal, TypeAlias, TypeVar

if TYPE_CHECKING:
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.lights.sources.ambient import AmbientLight
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight


LightNode: TypeAlias = "AmbientLight | DirectionalLight | PointLight | SpotLight"
T = TypeVar("T", bound="LightNode")


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

    view_name: str
    pass_name: str

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

    view_suffix: str = "shadow_view"
    pass_suffix: str = "shadow_pass"

    texture_uniform: str = "shadow_texture"
    view_uniform: str = "shadow_view_mat"
    projection_uniform: str = "shadow_projection_mat"

    bias: float = 0.005
    normal_bias: float = 0.05

    def create(self, light_name: str) -> ShadowConfig:
        return ShadowConfig(
            shader=self.shader,
            enabled=self.enabled,
            resolution=self.resolution,
            caster_tags=frozenset(self.caster_tags),
            receiver_tags=frozenset(self.receiver_tags),
            view_name=f"{light_name}.{self.view_suffix}",
            pass_name=f"{light_name}.{self.pass_suffix}",
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
class LightTemplate(Generic[T]):
    source: type[T]

    affected_tags: set[str] = field(default_factory=lambda: {"lit"})
    shadow_template: ShadowTemplate | None = None

    def create(
        self,
        *,
        name: str,
        **kwargs,
    ) -> T:
        node = self.source(
            name=name,
            **kwargs,
        )

        node.config = LightConfig(
            affected_tags=frozenset(self.affected_tags),
            shadow=(
                self.shadow_template.create(name)
                if self.shadow_template is not None
                else None
            ),
        )

        return node




