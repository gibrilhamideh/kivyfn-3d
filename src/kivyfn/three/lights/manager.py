# kivyfn/three/lights/manager.py

from __future__ import annotations

from math import cos, radians
from typing import TYPE_CHECKING, Any

from kivy.event import EventDispatcher

from kivyfn.three.lights.registry import LightRegistry
from kivyfn.three.lights.culling import LightCuller

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject, LightName, RenderPassName, ViewName
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.views.view import View
    from kivyfn.three.lights.culling import CulledLights
    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.lights.template import ShadowConfig


class LightManager(EventDispatcher):

    def __init__(
        self,
        renderer: Renderer,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.renderer = renderer
        self.registry = LightRegistry()
        self.culler = LightCuller(self.registry)

        self._shadow_views: dict[LightName, ViewName] = {}
        self._shadow_passes: dict[LightName, RenderPassName] = {}

        self._bound_ids: set[int] = set()

    def __repr__(self) -> str:
        return (
            "LightManager("
            f"lights={len(self.registry)}"
            ")"
        )

    # =================================== #
    # Lifecycle
    # =================================== #
    def create(
        self,
        node: SceneObject,
    ) -> None:
        changed = False

        for light in node.walk(filter="lights"):
            light_id = id(light)

            if light_id in self._bound_ids:
                continue

            self.registry.add(light)
            self._bound_ids.add(light_id)

            config = light.config.shadow
            if config is not None and config.enabled:
                self._create_shadow_resources(
                    light=light,
                    config=config,
                )

            light.bind(on_light_dirty=self.on_light_dirty)
            light.bind(on_transform_dirty=self.on_transform_dirty)
            light.bind(on_visibility_dirty=self.on_visibility_dirty)

            self.sync_transform(light)
            self.sync_visibility(light)

            changed = True

        if changed:
            self.sync_uniforms()

    # =================================== #
    # Dirty
    # =================================== #
    def on_light_dirty(
        self,
        light: Light3D,
    ) -> None:
        self.sync_visibility(light)
        self.sync_uniforms()

    def on_transform_dirty(
        self,
        light: Light3D,
    ) -> None:
        self.sync_transform(light)
        self.sync_uniforms()

    def on_visibility_dirty(
        self,
        light: Light3D,
    ) -> None:
        self.sync_visibility(light)
        self.sync_uniforms()

    # =================================== #
    # Sync
    # =================================== #
    def sync_transform(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            light_name = self.registry.name_of(light)

            if light_name is None:
                continue

            view_name = self._shadow_views.get(light_name)

            if view_name is None:
                continue

            view = self.renderer.views.require(view_name)

            position = light.world_position
            target = position + light.world_forward

            view.set_look_at(
                position=position,
                target=target,
            )

            self._sync_shadow_uniforms(light)

    def sync_visibility(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            self._sync_light_visibility(light)

    def sync_uniforms(self) -> None:
        affected_tags = self._affected_tags()

        if not affected_tags:
            return

        for stage in self.renderer.stages.select_contexts(tags=affected_tags):
            view = self._stage_view(stage)

            tags = self.renderer.stages.registry.tags_of(stage.name)
            culled = self.culler.select(
                stage_tags=tags,
                view=view,
            )

            uniforms = self._build_light_uniforms(culled)
            self._apply_uniforms(
                stage=stage,
                uniforms=uniforms,
            )

    # =================================== #
    # Visibility
    # =================================== #
    def _sync_light_visibility(
        self,
        light: Light3D,
    ) -> None:
        light_name = self.registry.name_of(light)

        if light_name is None:
            return

        pass_name = self._shadow_passes.get(light_name)

        if pass_name is None:
            return

        if light.enabled and light.visible_in_tree:
            self.renderer.show_stage(pass_name)
        else:
            self.renderer.hide_stage(pass_name)

    # =================================== #
    # Shadow Resources
    # =================================== #
    def _create_shadow_resources(
        self,
        *,
        light: Light3D,
        config: ShadowConfig,
    ) -> None:
        light_name = self.registry.require_name_of(light)

        view_name = self.registry.shadow_view_name(light_name)
        pass_name = self.registry.shadow_pass_name(light_name)

        view_config = config.view

        view = self.renderer.views.create(
            name=view_name,
            position=light.world_position,
            target=light.world_position + light.world_forward,
            projection_type=view_config.projection_type,
            near=view_config.near,
            far=view_config.far,
            ortho_size=view_config.ortho_size,
            fov=view_config.fov,
        )

        shadow_pass = self.renderer.create_pass(
            name=pass_name,
            view_name=view.name,
            shader=config.shader,
            output="depth",
            output_uniform=config.texture_uniform,

            local_viewport_width=config.resolution,
            local_viewport_height=config.resolution,
            use_local_viewport=True,
            size_to_viewport=True,

            tags=None,

            with_depthbuffer=True,
            with_stencilbuffer=False,
            clear_color=True,
            clear_depth=True,
            clear_stencil=False,
        )

        self.renderer.attach_pass(
            name=shadow_pass.name,
            target_tags=set(config.receiver_tags),
        )

        self.renderer.link_stage(
            source=shadow_pass.name,
            target_tags=set(config.caster_tags),
        )

        self._shadow_views[light_name] = view.name
        self._shadow_passes[light_name] = shadow_pass.name

        self._sync_shadow_uniforms(light)

    def _sync_shadow_uniforms(
        self,
        light: Light3D,
    ) -> None:
        config = light.config.shadow

        if config is None:
            return

        light_name = self.registry.name_of(light)

        if light_name is None:
            return

        view_name = self._shadow_views.get(light_name)

        if view_name is None:
            return

        view = self.renderer.views.require(view_name)

        self._apply_uniforms_to_tags(
            tags=set(config.receiver_tags),
            uniforms={
                config.view_uniform: view.get_view_matrix(),
                config.projection_uniform: view.get_projection_matrix(1.0),
                "shadow_bias": config.bias,
                "shadow_normal_bias": config.normal_bias,
            },
        )

    # =================================== #
    # Uniforms
    # =================================== #
    def _build_light_uniforms(
        self,
        lights: CulledLights,
    ) -> dict[str, Any]:
        max_directional = self.culler.limits.directional
        max_point = self.culler.limits.point
        max_spot = self.culler.limits.spot

        directional = lights.directional[:max_directional]
        point = lights.point[:max_point]
        spot = lights.spot[:max_spot]

        return {
            "directional_light_count": len(directional),
            "directional_light_directions": self._pad_vec3(
                [light.direction for light in directional],
                max_directional,
            ),
            "directional_light_colors": self._pad_color3(
                [light.color for light in directional],
                max_directional,
            ),
            "directional_light_intensities": self._pad_float(
                [light.intensity for light in directional],
                max_directional,
            ),

            "point_light_count": len(point),
            "point_light_positions": self._pad_vec3(
                [light.world_position for light in point],
                max_point,
            ),
            "point_light_colors": self._pad_color3(
                [light.color for light in point],
                max_point,
            ),
            "point_light_intensities": self._pad_float(
                [light.intensity for light in point],
                max_point,
            ),
            "point_light_radii": self._pad_float(
                [light.radius for light in point],
                max_point,
            ),

            "spot_light_count": len(spot),
            "spot_light_positions": self._pad_vec3(
                [light.world_position for light in spot],
                max_spot,
            ),
            "spot_light_directions": self._pad_vec3(
                [light.direction for light in spot],
                max_spot,
            ),
            "spot_light_colors": self._pad_color3(
                [light.color for light in spot],
                max_spot,
            ),
            "spot_light_intensities": self._pad_float(
                [light.intensity for light in spot],
                max_spot,
            ),
            "spot_light_radii": self._pad_float(
                [light.radius for light in spot],
                max_spot,
            ),
            "spot_light_angles": self._pad_float(
                [light.angle for light in spot],
                max_spot,
            ),
            "spot_light_angle_cos": self._pad_float(
                [cos(radians(light.angle)) for light in spot],
                max_spot,
            ),
        }

    # =================================== #
    # Stage Helpers
    # =================================== #
    def _affected_tags(self) -> set[str]:
        tags: set[str] = set()

        for light in self.registry.values():
            tags.update(light.config.affected_tags)

        return tags

    def _stage_view(
        self,
        stage: RenderContext,
    ) -> View | None:
        return self.renderer.views.view_for_stage(
            stage.name,
        )

    def _apply_uniforms_to_tags(
        self,
        *,
        tags: set[str],
        uniforms: dict[str, Any],
    ) -> None:
        for stage in self.renderer.stages.select_contexts(tags=tags):
            self._apply_uniforms(
                stage=stage,
                uniforms=uniforms,
            )

    def _apply_uniforms(
        self,
        *,
        stage: RenderContext,
        uniforms: dict[str, Any],
    ) -> None:
        for name, value in uniforms.items():
            stage.apply_uniform(name, value)

    # =================================== #
    # Packing Helpers
    # =================================== #
    def _pad_vec3(
        self,
        values: list[Any],
        size: int,
    ) -> list[list[float]]:
        result: list[list[float]] = []

        for value in values:
            result.append([
                float(value.x),
                float(value.y),
                float(value.z),
            ])

        missing = size - len(values)
        if missing > 0:
            result.extend([[0.0, 0.0, 0.0] for _ in range(missing)])

        return result

    def _pad_color3(
        self,
        values: list[Any],
        size: int,
    ) -> list[list[float]]:
        result: list[list[float]] = []

        for value in values:
            result.append([
                float(value[0]),
                float(value[1]),
                float(value[2]),
            ])

        missing = size - len(values)
        if missing > 0:
            result.extend([[0.0, 0.0, 0.0] for _ in range(missing)])

        return result

    def _pad_float(
        self,
        values: list[float],
        size: int,
    ) -> list[float]:
        result = [float(value) for value in values]

        missing = size - len(values)
        if missing > 0:
            result.extend([0.0] * missing)

        return result
