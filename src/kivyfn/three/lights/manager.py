# kivyfn/three/lights/manager.py

from __future__ import annotations

from math import cos, radians
from typing import TYPE_CHECKING, Any, cast

from kivy.event import EventDispatcher
from kivy.clock import Clock

from kivyfn.three.lights.registry import LightRegistry
from kivyfn.three.lights.culling import LightCuller
from kivyfn.three.types import LightSource

if TYPE_CHECKING:
    from kivyfn.three.lights.limits import LightLimits
    from kivyfn.three.types import SceneObject, LightName, RenderPassName, ViewName
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.lights.culling import CulledLights
    from kivyfn.three.lights.template import ShadowConfig
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.point import PointLight
    from kivyfn.three.lights.sources.spot import SpotLight


class LightUniformBuffer:

    def __init__(
        self,
        limits: LightLimits,
    ) -> None:
        self.directional_directions = self._vec3(limits.directional)
        self.directional_colors = self._vec3(limits.directional)
        self.directional_intensities = self._floats(limits.directional)

        self.point_positions = self._vec3(limits.point)
        self.point_colors = self._vec3(limits.point)
        self.point_intensities = self._floats(limits.point)
        self.point_radii = self._floats(limits.point)

        self.spot_positions = self._vec3(limits.spot)
        self.spot_directions = self._vec3(limits.spot)
        self.spot_colors = self._vec3(limits.spot)
        self.spot_intensities = self._floats(limits.spot)
        self.spot_radii = self._floats(limits.spot)
        self.spot_angles = self._floats(limits.spot)
        self.spot_angle_cos = self._floats(limits.spot)

    def _vec3(
        self,
        size: int,
    ) -> list[list[float]]:
        return [
            [0.0, 0.0, 0.0]
            for _ in range(size)
        ]

    def _floats(
        self,
        size: int,
    ) -> list[float]:
        return [
            0.0
            for _ in range(size)
        ]


class LightManager(EventDispatcher):

    def __init__(
        self,
        renderer: Renderer,
        *,
        limits: LightLimits,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.renderer = renderer

        self.registry = LightRegistry()
        self.uniforms = LightUniformBuffer(limits)
        self.culler = LightCuller(limits=limits)

        self._shadow_views: dict[LightName, ViewName] = {}
        self._shadow_passes: dict[LightName, RenderPassName] = {}

        self._bound_ids: set[int] = set()

        self._sync_uniforms_trigger = Clock.create_trigger(self.sync_uniforms, -1)

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
            light = cast("LightSource", light)

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
            self._sync_uniforms_trigger()

    def destroy(
        self,
        node: SceneObject,
    ) -> None:
        changed = False

        for light in list(node.walk(filter="lights")):
            light = cast("LightSource", light)

            light_name = self.registry.name_of(light)
            if light_name is None:
                continue

            light.unbind(
                on_light_dirty=self.on_light_dirty,
            )
            light.unbind(
                on_transform_dirty=self.on_transform_dirty,
            )
            light.unbind(
                on_visibility_dirty=self.on_visibility_dirty,
            )

            self._bound_ids.discard(id(light))

            shadow_pass = self._shadow_passes.pop(
                light_name,
                None,
            )

            shadow_view = self._shadow_views.pop(
                light_name,
                None,
            )

            if (
                shadow_pass is not None
                and self.renderer.stages.get(shadow_pass) is not None
            ):
                self.renderer.destroy_stage(
                    shadow_pass,
                )

            if (
                shadow_view is not None
                and self.renderer.views.get(shadow_view) is not None
            ):
                self.renderer.views.destroy(
                    shadow_view,
                )

            self.registry.remove(light_name)

            changed = True

        if changed:
            self._sync_uniforms_trigger()

    # =================================== #
    # Dirty
    # =================================== #
    def on_light_dirty(
        self,
        light: LightSource,
    ) -> None:
        self.sync_visibility(light)
        self._sync_uniforms_trigger()

    def on_transform_dirty(
        self,
        light: LightSource,
    ) -> None:
        self.sync_transform(light)
        self._sync_uniforms_trigger()

    def on_visibility_dirty(
        self,
        light: LightSource,
    ) -> None:
        self.sync_visibility(light)
        self._sync_uniforms_trigger()

    # =================================== #
    # Sync Transform
    # =================================== #
    def sync_transform(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):

            light = cast("LightSource", light)

            light_name = self.registry.name_of(light)
            if light_name is None:
                continue

            view_name = self._shadow_views.get(light_name)
            if view_name is None:
                continue


            position = light.world_position
            target = position + light.world_forward

            view = self.renderer.views.require(view_name)
            view.set_look_at(
                position=position,
                target=target,
            )

            self.sync_shadow_uniforms(light)

    # =================================== #
    # Sync Visibility
    # =================================== #
    def sync_visibility(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):

            light = cast("LightSource", light)

            light_name = self.registry.name_of(light)
            if light_name is None:
                continue

            pass_name = self._shadow_passes.get(light_name)
            if pass_name is None:
                continue

            if light.enabled and light.visible_in_tree:
                self.renderer.show_stage(pass_name)
            else:
                self.renderer.hide_stage(pass_name)

    # =================================== #
    # Sync Uniforms
    # =================================== #
    def sync_uniforms(self, *_) -> None:
        affected_tags = self.registry.affected_tags()
        if not affected_tags:
            return

        seen: dict[tuple[str, frozenset[str]], CulledLights] = {}

        for stage in self.renderer.stages.select_contexts(tags=affected_tags):
            view = self.renderer.views.view_for_stage(stage.name)
            tags = self.renderer.stages.registry.tags_of(stage.name)

            key = (view.name,frozenset(tags))
            culled = seen.get(key)

            if culled is None:
                candidates = self.registry.values_for_tags(tags)

                culled = self.culler.select(
                    lights=candidates,
                    view=view,
                )

                seen[key] = culled

            uniforms = self._build_light_uniforms(culled)
            self._apply_uniforms(
                stage=stage,
                uniforms=uniforms,
            )


    def sync_shadow_uniforms(
        self,
        light: LightSource,
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
                config.view_uniform: view.get_view_matrix().to_uniform(),
                config.projection_uniform: view.get_projection_matrix(1.0).to_uniform(),
                "shadow_bias": config.bias,
                "shadow_normal_bias": config.normal_bias,
            },
        )

    # =================================== #
    # Shadow Resources
    # =================================== #
    def _create_shadow_resources(
        self,
        *,
        light: LightSource,
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

        self.sync_shadow_uniforms(light)

    # =================================== #
    # Uniforms
    # =================================== #
    def _build_light_uniforms(
        self,
        lights: CulledLights,
    ) -> dict[str, Any]:
        directional = lights.directional
        point = lights.point
        spot = lights.spot

        self._write_directional_lights(directional)
        self._write_point_lights(point)
        self._write_spot_lights(spot)

        return {
            "directional_light_count": len(directional),
            "directional_light_directions": self.uniforms.directional_directions,
            "directional_light_colors": self.uniforms.directional_colors,
            "directional_light_intensities": self.uniforms.directional_intensities,

            "point_light_count": len(point),
            "point_light_positions": self.uniforms.point_positions,
            "point_light_colors": self.uniforms.point_colors,
            "point_light_intensities": self.uniforms.point_intensities,
            "point_light_radii": self.uniforms.point_radii,

            "spot_light_count": len(spot),
            "spot_light_positions": self.uniforms.spot_positions,
            "spot_light_directions": self.uniforms.spot_directions,
            "spot_light_colors": self.uniforms.spot_colors,
            "spot_light_intensities": self.uniforms.spot_intensities,
            "spot_light_radii": self.uniforms.spot_radii,
            "spot_light_angles": self.uniforms.spot_angles,
            "spot_light_angle_cos": self.uniforms.spot_angle_cos,
        }

    def _write_directional_lights(
        self,
        lights: list[DirectionalLight],
    ) -> None:
        for index, light in enumerate(lights):
            direction = light.world_forward
            color = light.color

            target = self.uniforms.directional_directions[index]
            target[0] = float(direction.x)
            target[1] = float(direction.y)
            target[2] = float(direction.z)

            target = self.uniforms.directional_colors[index]
            target[0] = float(color[0])
            target[1] = float(color[1])
            target[2] = float(color[2])

            self.uniforms.directional_intensities[index] = float(
                light.intensity
            )

    def _write_point_lights(
        self,
        lights: list[PointLight],
    ) -> None:
        for index, light in enumerate(lights):
            position = light.world_position
            color = light.color

            target = self.uniforms.point_positions[index]
            target[0] = float(position.x)
            target[1] = float(position.y)
            target[2] = float(position.z)

            target = self.uniforms.point_colors[index]
            target[0] = float(color[0])
            target[1] = float(color[1])
            target[2] = float(color[2])

            self.uniforms.point_intensities[index] = float(
                light.intensity
            )
            self.uniforms.point_radii[index] = float(
                light.radius
            )

    def _write_spot_lights(
        self,
        lights: list[SpotLight],
    ) -> None:
        for index, light in enumerate(lights):
            position = light.world_position
            direction = light.direction
            color = light.color

            target = self.uniforms.spot_positions[index]
            target[0] = float(position.x)
            target[1] = float(position.y)
            target[2] = float(position.z)

            target = self.uniforms.spot_directions[index]
            target[0] = float(direction.x)
            target[1] = float(direction.y)
            target[2] = float(direction.z)

            target = self.uniforms.spot_colors[index]
            target[0] = float(color[0])
            target[1] = float(color[1])
            target[2] = float(color[2])

            angle = float(light.angle)

            self.uniforms.spot_intensities[index] = float(
                light.intensity
            )
            self.uniforms.spot_radii[index] = float(
                light.radius
            )
            self.uniforms.spot_angles[index] = angle
            self.uniforms.spot_angle_cos[index] = cos(
                radians(angle)
            )

    # =================================== #
    # Stage Helpers
    # =================================== #
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
