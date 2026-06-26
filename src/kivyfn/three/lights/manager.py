# kivyfn/three/lights/manager.py

from __future__ import annotations

from math import cos, radians
from typing import TYPE_CHECKING, Any, cast

from kivy.clock import Clock
from kivy.event import EventDispatcher

from kivyfn.three.lights.culling import LightCuller
from kivyfn.three.lights.registry import LightRegistry
from kivyfn.three.lights.sources.point import PointLight
from kivyfn.three.render.context import (
    RenderContext,
    RenderPass2D,
    RenderPassCube,
)
from kivyfn.three.types import LightSource

if TYPE_CHECKING:
    from kivyfn.three.lights.culling import CulledLights
    from kivyfn.three.lights.limits import LightLimits
    from kivyfn.three.lights.sources.directional import DirectionalLight
    from kivyfn.three.lights.sources.spot import SpotLight
    from kivyfn.three.lights.template import ShadowConfig
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.types import SceneObject


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

        self._shadow_passes: dict[str, str] = {}
        self._bound_ids: set[int] = set()

        self._uniform_trigger = Clock.create_trigger(
            self.sync_uniforms,
            -1,
        )

    def __repr__(self) -> str:
        return (
            "LightManager("
            f"lights={len(self.registry)}"
            ")"
        )

    # =================================== #
    # Lifecycle
    # =================================== #
    def attach(
        self,
        node: SceneObject,
    ) -> None:
        changed = False

        for light in node.walk(filter="lights"):
            light = cast("LightSource", light)

            light_id = id(light)

            if light_id in self._bound_ids:
                raise ValueError(
                    f"Light {light.name!r} is already attached."
                )

            self.registry.add(light)
            self._bound_ids.add(light_id)

            config = light.config.shadow
            if config is not None and config.enabled:
                self._create_shadow_resources(
                    light=light,
                    config=config,
                )

            light.bind(
                on_light_dirty=self.on_light_dirty,
            )
            light.bind(
                on_transform_dirty=self.on_transform_dirty,
            )
            light.bind(
                on_visibility_dirty=self.on_visibility_dirty,
            )

            self.sync_transform(light)
            self.sync_visibility(light)

            changed = True

        if changed:
            self._uniform_trigger()

    def detach(
        self,
        node: SceneObject,
    ) -> None:
        changed = False

        for light in list(node.walk(filter="lights")):
            light = cast("LightSource", light)

            light_id = id(light)

            if light_id not in self._bound_ids:
                raise ValueError(
                    f"Light {light.name!r} is not attached."
                )

            light.unbind(
                on_light_dirty=self.on_light_dirty,
            )
            light.unbind(
                on_transform_dirty=self.on_transform_dirty,
            )
            light.unbind(
                on_visibility_dirty=self.on_visibility_dirty,
            )

            self._bound_ids.discard(light_id)

            shadow_pass = self._shadow_passes.pop(
                light.name,
                None,
            )

            if (
                shadow_pass is not None
                and self.renderer.stages.registry.get(shadow_pass) is not None
            ):
                self.renderer.remove_stage(
                    shadow_pass,
                )

            self.registry.remove(light.name)

            changed = True

        if changed:
            self._uniform_trigger()

    # =================================== #
    # Dirty
    # =================================== #
    def on_light_dirty(
        self,
        light: LightSource,
    ) -> None:
        self._uniform_trigger()

    def on_transform_dirty(
        self,
        light: LightSource,
    ) -> None:
        self.sync_transform(light)
        self._uniform_trigger()

    def on_visibility_dirty(
        self,
        light: LightSource,
    ) -> None:
        self.sync_visibility(light)
        self._uniform_trigger()

    # =================================== #
    # Sync Transform
    # =================================== #
    def sync_transform(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            light = cast("LightSource", light)

            pass_name = self._shadow_passes.get(light.name)
            if pass_name is None:
                continue

            shadow_pass = self.renderer.stages.registry.require(pass_name)

            if isinstance(shadow_pass, RenderPassCube):
                shadow_pass.view.position = light.world_position
                self.sync_shadow_uniforms(light)
                continue

            if isinstance(shadow_pass, RenderPass2D):
                position = light.world_position
                target = position + light.world_forward

                shadow_pass.view.set_look_at(
                    position=position,
                    target=target,
                )

                self.sync_shadow_uniforms(light)
                continue

            raise TypeError(
                f"Shadow stage {pass_name!r} is not a shadow pass."
            )

    # =================================== #
    # Sync Visibility
    # =================================== #
    def sync_visibility(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            light = cast("LightSource", light)

            pass_name = self._shadow_passes.get(light.name)
            if pass_name is None:
                continue

            if light.enabled and light.visible_in_tree:
                self.renderer.show_stage(pass_name)
            else:
                self.renderer.hide_stage(pass_name)

    # =================================== #
    # Sync Uniforms
    # =================================== #
    def sync_uniforms(
        self,
        *_,
    ) -> None:
        affected_tags = self.registry.tags()
        if not affected_tags:
            return

        contexts: dict[str, RenderContext] = {}

        for tag in affected_tags:
            for stage in self.renderer.stages.registry.contexts_of(tag):
                contexts[stage.name] = stage

        seen: dict[tuple[int, frozenset[str]], CulledLights] = {}

        for stage in contexts.values():
            tags = self.renderer.stages.registry.tags_of(stage.name)

            view = stage.require_planar_view()

            key = (
                id(view),
                frozenset(tags),
            )

            culled = seen.get(key)

            if culled is None:
                candidates_by_id: dict[int, LightSource] = {}

                for tag in tags:
                    for light in self.registry.lights_of(tag):
                        candidates_by_id[id(light)] = light

                candidates = list(candidates_by_id.values())

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

        pass_name = self._shadow_passes.get(light.name)
        if pass_name is None:
            return

        shadow_pass = self.renderer.stages.registry.require(pass_name)

        if isinstance(shadow_pass, RenderPassCube):
            self._apply_uniforms_to_tags(
                tags=set(config.receiver_tags),
                uniforms={
                    "shadow_bias": config.bias,
                    "shadow_normal_bias": config.normal_bias,
                    "shadow_far": shadow_pass.view.far,
                },
            )

            shadow_pass.apply_uniform(
                "shadow_far",
                shadow_pass.view.far,
            )
            return

        if isinstance(shadow_pass, RenderPass2D):
            view = shadow_pass.view

            self._apply_uniforms_to_tags(
                tags=set(config.receiver_tags),
                uniforms={
                    config.view_uniform: view.get_view_matrix().to_uniform(),
                    config.projection_uniform: view.get_projection_matrix(
                        shadow_pass.render_aspect,
                    ).to_uniform(),
                    "shadow_bias": config.bias,
                    "shadow_normal_bias": config.normal_bias,
                },
            )
            return

        raise TypeError(
            f"Shadow stage {pass_name!r} is not a shadow pass."
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
        if isinstance(light, PointLight):
            self._create_point_shadow_resources(
                light=light,
                config=config,
            )
            return

        self._create_planar_shadow_resources(
            light=light,
            config=config,
        )

    def _create_planar_shadow_resources(
        self,
        *,
        light: LightSource,
        config: ShadowConfig,
    ) -> None:
        pass_name = light.name
        view_config = config.view

        shadow_pass = self.renderer.create_pass(
            name=pass_name,
            camera=None,
            shader=config.shader,
            output="depth",
            output_uniform=config.texture_uniform,
            size=[
                config.resolution,
                config.resolution,
            ],
            tags=set(config.caster_tags),
            push_viewport=True,
            with_depthbuffer=True,
            with_stencilbuffer=False,
            clear_color=(0.0, 0.0, 0.0, 0.0),
            clear_color_buffer=True,
            clear_depth_buffer=True,
            clear_stencil_buffer=False,
        )

        view = shadow_pass.view

        view.set_look_at(
            position=light.world_position,
            target=light.world_position + light.world_forward,
        )

        view.projection = view_config.projection
        view.near = view_config.near
        view.far = view_config.far
        view.ortho_size = view_config.ortho_size
        view.fov = view_config.fov

        shadow_pass.sync_view()

        self.renderer.attach_pass(
            name=shadow_pass.name,
            target_tags=set(config.receiver_tags),
        )

        self._shadow_passes[light.name] = shadow_pass.name

        self.sync_shadow_uniforms(light)

    def _create_point_shadow_resources(
        self,
        *,
        light: PointLight,
        config: ShadowConfig,
    ) -> None:
        pass_name = light.name

        shadow_pass = self.renderer.create_cube_pass(
            name=pass_name,
            shader=config.shader,
            output="depth",
            output_uniform=config.texture_uniform,
            size=config.resolution,
            tags=set(config.caster_tags),
            push_viewport=True,
            with_depthbuffer=True,
            with_stencilbuffer=False,
            clear_color=(0.0, 0.0, 0.0, 0.0),
            clear_color_buffer=True,
            clear_depth_buffer=True,
            clear_stencil_buffer=False,
        )

        shadow_pass.view.position = light.world_position
        shadow_pass.view.near = config.view.near
        shadow_pass.view.far = config.view.far

        shadow_pass.sync_view()

        self.renderer.attach_pass(
            name=shadow_pass.name,
            target_tags=set(config.receiver_tags),
        )

        self._shadow_passes[light.name] = shadow_pass.name
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
                light.intensity,
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
                light.intensity,
            )
            self.uniforms.point_radii[index] = float(
                light.radius,
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
                light.intensity,
            )
            self.uniforms.spot_radii[index] = float(
                light.radius,
            )
            self.uniforms.spot_angles[index] = angle
            self.uniforms.spot_angle_cos[index] = cos(
                radians(angle),
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
        contexts: dict[str, RenderContext] = {}

        for tag in tags:
            for stage in self.renderer.stages.registry.contexts_of(tag):
                contexts[stage.name] = stage

        for stage in contexts.values():
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
            stage.apply_uniform(
                name,
                value,
            )
