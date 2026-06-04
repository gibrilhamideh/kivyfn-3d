# kivyfn/three/lights/manager.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivy.event import EventDispatcher

from kivyfn.three.lights.registry import LightRegistry
from kivyfn.three.lights.selection import LightSelection
from kivyfn.three.lights.shadow import LightShadow
from kivyfn.three.lights.sources.ambient import AmbientLight
from kivyfn.three.lights.sources.base import Light3D
from kivyfn.three.lights.sources.directional import DirectionalLight
from kivyfn.three.lights.sources.point import PointLight
from kivyfn.three.lights.sources.spot import SpotLight
from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.render.context import RenderContext
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.views.view import View


class LightManager(EventDispatcher):

    __events__ = (
        "on_light_dirty",
    )

    POINT_FACE_DIRECTIONS: tuple[Vector3, ...] = (
        Vector3(1.0, 0.0, 0.0),
        Vector3(-1.0, 0.0, 0.0),
        Vector3(0.0, 1.0, 0.0),
        Vector3(0.0, -1.0, 0.0),
        Vector3(0.0, 0.0, 1.0),
        Vector3(0.0, 0.0, -1.0),
    )

    POINT_FACE_UPS: tuple[Vector3, ...] = (
        Vector3(0.0, -1.0, 0.0),
        Vector3(0.0, -1.0, 0.0),
        Vector3(0.0, 0.0, 1.0),
        Vector3(0.0, 0.0, -1.0),
        Vector3(0.0, -1.0, 0.0),
        Vector3(0.0, -1.0, 0.0),
    )

    POINT_FACE_NAMES: tuple[str, ...] = (
        "px",
        "nx",
        "py",
        "ny",
        "pz",
        "nz",
    )

    def __init__(
        self,
        renderer: Renderer,
        *,
        max_point_lights: int = 8,
        max_spot_lights: int = 8,
    ) -> None:
        super().__init__()

        self.renderer = renderer
        self.registry = LightRegistry()

        self.max_point_lights = max_point_lights
        self.max_spot_lights = max_spot_lights

        self.renderer.views.bind(
            on_view_dirty=self._on_view_dirty,
        )

    def __len__(self) -> int:
        return len(self.registry)

    # =================================== #
    # Light API
    # =================================== #
    def add(
        self,
        light: Light3D,
        *,
        tags: set[str] | None = None,
        parent: Node3D | None = None,
        sync: bool = True,
    ) -> Light3D:
        if not light.name:
            raise ValueError("Light must have a name before registration.")

        if parent is not None:
            parent.add_child(light)

        self.registry.add(
            light,
            tags=tags,
        )

        light.bind(
            on_light_dirty=self._on_light_property_dirty,
            on_transform_dirty=self._on_light_transform_dirty,
            on_visibility_dirty=self._on_light_visibility_dirty,
        )

        if sync:
            self.sync_light(light)

        return light

    def remove(
        self,
        name: str,
        *,
        sync: bool = True,
    ) -> Light3D:
        record = self.registry.remove(name)
        light = record.light

        light.unbind(
            on_light_dirty=self._on_light_property_dirty,
            on_transform_dirty=self._on_light_transform_dirty,
            on_visibility_dirty=self._on_light_visibility_dirty,
        )

        shadow = getattr(record, "shadow", None)

        if shadow is not None:
            self._destroy_shadow_resources(shadow)

        if light.parent is not None:
            light.parent.remove_child(light)

        if sync:
            self.sync_all_contexts()

        return light

    def get(
        self,
        name: str,
    ) -> Light3D | None:
        record = self.registry.get(name)
        return record.light if record is not None else None

    def require(
        self,
        name: str,
    ) -> Light3D:
        return self.registry.require(name).light

    def values(self) -> list[Light3D]:
        return [
            record.light
            for record in self.registry.values()
        ]

    # =================================== #
    # Tags
    # =================================== #
    def add_tag(
        self,
        name: str,
        tag: str,
        *,
        sync: bool = True,
    ) -> None:
        self.registry.add_tag(
            name,
            tag,
        )

        if sync:
            self.sync_light(
                self.require(name),
            )

    def remove_tag(
        self,
        name: str,
        tag: str,
        *,
        sync: bool = True,
    ) -> None:
        self.registry.remove_tag(
            name,
            tag,
        )

        if sync:
            self.sync_all_contexts()

    # =================================== #
    # Shadow API
    # =================================== #
    def enable_shadow(
        self,
        name: str,
        *,
        shadow_shader: Any,
        resolution: int = 2048,
        caster_tags: set[str] | None = None,
        receiver_tags: set[str] | None = None,
        texture_uniform: str | None = None,
        view_uniform: str | None = None,
        projection_uniform: str | None = None,
        target: Vector3 | None = None,
        distance: float = 512.0,
        near: float = 0.1,
        far: float = 1024.0,
        ortho_size: float = 256.0,
        bias: float = 0.005,
        normal_bias: float = 0.05,
        pass_kwargs: dict[str, Any] | None = None,
    ) -> LightShadow:
        record = self.registry.require(name)
        light = record.light

        if isinstance(light, AmbientLight):
            raise TypeError("AmbientLight cannot cast shadows.")

        if isinstance(light, DirectionalLight):
            shadow_type = "directional"
            view_names = (f"{name}-shadow-view",)
            pass_names = (f"{name}-shadow-pass",)

        elif isinstance(light, SpotLight):
            shadow_type = "spot"
            view_names = (f"{name}-shadow-view",)
            pass_names = (f"{name}-shadow-pass",)

        elif isinstance(light, PointLight):
            shadow_type = "point"
            view_names = tuple(
                f"{name}-shadow-{face}-view"
                for face in self.POINT_FACE_NAMES
            )
            pass_names = tuple(
                f"{name}-shadow-{face}-pass"
                for face in self.POINT_FACE_NAMES
            )

        else:
            raise TypeError(
                f"Unsupported shadow light type: {type(light).__name__}"
            )

        shadow = LightShadow(
            shadow_type=shadow_type,
            resolution=resolution,
            caster_tags=set(caster_tags or ()),
            receiver_tags=set(receiver_tags or ()),
            view_names=view_names,
            pass_names=pass_names,
            texture_uniform=texture_uniform or f"{name}_shadow_texture",
            view_uniform=view_uniform or f"{name}_shadow_view_mat",
            projection_uniform=(
                projection_uniform or f"{name}_shadow_projection_mat"
            ),
            target=target or Vector3.zero(),
            distance=distance,
            near=near,
            far=far,
            ortho_size=ortho_size,
            bias=bias,
            normal_bias=normal_bias,
        )

        record.shadow = shadow

        self._create_shadow_resources(
            light=light,
            shadow=shadow,
            shadow_shader=shadow_shader,
            pass_kwargs=pass_kwargs or {},
        )

        self._update_shadow_views(
            light,
            shadow,
        )

        self.sync_light(light)

        return shadow

    def disable_shadow(
        self,
        name: str,
        *,
        sync: bool = True,
    ) -> LightShadow | None:
        record = self.registry.require(name)
        shadow = getattr(record, "shadow", None)

        if shadow is None:
            return None

        record.shadow = None

        self._destroy_shadow_resources(shadow)

        if sync:
            self.sync_light(record.light)

        return shadow

    # =================================== #
    # Selection
    # =================================== #
    def select(
        self,
        stage: RenderContext,
        view: View,
    ) -> LightSelection:
        selection = LightSelection()

        stage_tags = getattr(stage, "tags", set())

        for record in self.registry.values():
            light = record.light

            if not light.enabled:
                continue

            if not light.visible_in_tree:
                continue

            if record.tags and not record.tags.intersection(stage_tags):
                continue

            if isinstance(light, AmbientLight):
                if not selection.ambient:
                    selection.ambient.append(light)
                continue

            if isinstance(light, DirectionalLight):
                if not selection.directional:
                    selection.directional.append(light)
                continue

            if isinstance(light, PointLight):
                if self._select_point_light(
                    light,
                    stage,
                    view,
                ):
                    selection.point.append(light)
                continue

            if isinstance(light, SpotLight):
                if self._select_spot_light(
                    light,
                    stage,
                    view,
                ):
                    selection.spot.append(light)
                continue

        selection.point[:] = selection.point[:self.max_point_lights]
        selection.spot[:] = selection.spot[:self.max_spot_lights]

        return selection

    # =================================== #
    # Sync
    # =================================== #
    def sync_light(
        self,
        light: Light3D,
    ) -> None:
        for stage in self._affected_contexts(light):
            self.sync_context(stage.name)

        record = self.registry.get(light.name)
        if record is None:
            return

        shadow = getattr(record, "shadow", None)

        if shadow is not None:
            self._update_shadow_views(
                light,
                shadow,
            )

    def sync_context(
        self,
        name: str,
    ) -> None:
        stage = self._get_context(name)

        if stage is None:
            return

        view = self.renderer.views.view_for_stage(name)

        if view is None:
            return

        selection = self.select(
            stage,
            view,
        )

        self._upload_selection(
            stage,
            selection,
        )

    def sync_all_contexts(self) -> None:
        for stage in self._contexts():
            self.sync_context(stage.name)

    # =================================== #
    # Events
    # =================================== #
    def _on_light_property_dirty(
        self,
        light: Light3D,
        *_,
    ) -> None:
        self.sync_light(light)
        self.dispatch(
            "on_light_dirty",
            light,
        )

    def _on_light_transform_dirty(
        self,
        light: Light3D,
        *_,
    ) -> None:
        self.sync_light(light)
        self.dispatch(
            "on_light_dirty",
            light,
        )

    def _on_light_visibility_dirty(
        self,
        light: Light3D,
        *_,
    ) -> None:
        self.sync_light(light)
        self.dispatch(
            "on_light_dirty",
            light,
        )

    def _on_view_dirty(
        self,
        manager,
        view: View,
        name: str,
    ) -> None:
        self.sync_context(name)

    def on_light_dirty(
        self,
        light: Light3D,
    ) -> None:
        pass

    # =================================== #
    # Upload
    # =================================== #
    def _upload_selection(
        self,
        stage: RenderContext,
        selection: LightSelection,
    ) -> None:
        ambient = selection.ambient[0] if selection.ambient else None
        directional = (
            selection.directional[0]
            if selection.directional
            else None
        )

        stage.apply_uniform(
            "ambient_light_enabled",
            ambient is not None,
        )
        stage.apply_uniform(
            "ambient_light_color",
            list(ambient.color) if ambient is not None else [0.0, 0.0, 0.0],
        )
        stage.apply_uniform(
            "ambient_light_intensity",
            ambient.intensity if ambient is not None else 0.0,
        )

        stage.apply_uniform(
            "directional_light_enabled",
            directional is not None,
        )
        stage.apply_uniform(
            "directional_light_direction",
            (
                directional.direction.tolist()
                if directional is not None
                else [0.0, -1.0, 0.0]
            ),
        )
        stage.apply_uniform(
            "directional_light_color",
            (
                list(directional.color)
                if directional is not None
                else [0.0, 0.0, 0.0]
            ),
        )
        stage.apply_uniform(
            "directional_light_intensity",
            directional.intensity if directional is not None else 0.0,
        )

        self._upload_point_lights(
            stage,
            selection.point,
        )

        self._upload_spot_lights(
            stage,
            selection.spot,
        )

        self._upload_shadow_uniforms(
            stage,
        )

    def _upload_point_lights(
        self,
        stage: RenderContext,
        lights: list[PointLight],
    ) -> None:
        count = min(
            len(lights),
            self.max_point_lights,
        )

        stage.apply_uniform(
            "point_light_count",
            count,
        )

        for index in range(self.max_point_lights):
            light = lights[index] if index < count else None

            stage.apply_uniform(
                f"point_light_positions[{index}]",
                (
                    light.world_position.tolist()
                    if light is not None
                    else [0.0, 0.0, 0.0]
                ),
            )
            stage.apply_uniform(
                f"point_light_colors[{index}]",
                (
                    list(light.color)
                    if light is not None
                    else [0.0, 0.0, 0.0]
                ),
            )
            stage.apply_uniform(
                f"point_light_intensities[{index}]",
                light.intensity if light is not None else 0.0,
            )
            stage.apply_uniform(
                f"point_light_radii[{index}]",
                light.radius if light is not None else 0.0,
            )

    def _upload_spot_lights(
        self,
        stage: RenderContext,
        lights: list[SpotLight],
    ) -> None:
        count = min(
            len(lights),
            self.max_spot_lights,
        )

        stage.apply_uniform(
            "spot_light_count",
            count,
        )

        for index in range(self.max_spot_lights):
            light = lights[index] if index < count else None

            stage.apply_uniform(
                f"spot_light_positions[{index}]",
                (
                    light.world_position.tolist()
                    if light is not None
                    else [0.0, 0.0, 0.0]
                ),
            )
            stage.apply_uniform(
                f"spot_light_directions[{index}]",
                (
                    light.direction.tolist()
                    if light is not None
                    else [0.0, -1.0, 0.0]
                ),
            )
            stage.apply_uniform(
                f"spot_light_colors[{index}]",
                (
                    list(light.color)
                    if light is not None
                    else [0.0, 0.0, 0.0]
                ),
            )
            stage.apply_uniform(
                f"spot_light_intensities[{index}]",
                light.intensity if light is not None else 0.0,
            )
            stage.apply_uniform(
                f"spot_light_radii[{index}]",
                light.radius if light is not None else 0.0,
            )
            stage.apply_uniform(
                f"spot_light_angles[{index}]",
                light.angle if light is not None else 0.0,
            )

    def _upload_shadow_uniforms(
        self,
        stage: RenderContext,
    ) -> None:
        stage_tags = getattr(
            stage,
            "tags",
            set(),
        )

        for record in self.registry.values():
            shadow = getattr(record, "shadow", None)

            if shadow is None:
                continue

            receiver_tags = shadow.receiver_tags or set()

            if receiver_tags and not receiver_tags.intersection(stage_tags):
                continue

            if len(shadow.view_names) != 1:
                continue

            view = self.renderer.views.get(
                shadow.view_names[0],
            )

            stage.apply_uniform(
                shadow.view_uniform,
                view.get_view_matrix(),
            )
            stage.apply_uniform(
                shadow.projection_uniform,
                view.get_projection_matrix(1.0),
            )
            stage.apply_uniform(
                f"{shadow.texture_uniform}_bias",
                shadow.bias,
            )
            stage.apply_uniform(
                f"{shadow.texture_uniform}_normal_bias",
                shadow.normal_bias,
            )

    # =================================== #
    # Shadow Resources
    # =================================== #
    def _create_shadow_resources(
        self,
        *,
        light: Light3D,
        shadow: LightShadow,
        shadow_shader: Any,
        pass_kwargs: dict[str, Any],
    ) -> None:
        for view_name in shadow.view_names:
            if view_name in self.renderer.views:
                continue

            self.renderer.views.create(
                view_name,
                position=Vector3.zero(),
                target=Vector3(0.0, 0.0, -1.0),
                up=Vector3(0.0, 1.0, 0.0),
                near=shadow.near,
                far=shadow.far,
                ortho_size=shadow.ortho_size,
                projection_type=(
                    "orthographic"
                    if shadow.shadow_type == "directional"
                    else "perspective"
                ),
            )

        for pass_name, view_name in zip(
            shadow.pass_names,
            shadow.view_names,
        ):
            self.renderer.create_pass(
                name=pass_name,
                shader=shadow_shader,
                output="depth",
                tags={
                    "shadow",
                    f"shadow:{light.name}",
                },
                fbo_width=shadow.resolution,
                fbo_height=shadow.resolution,
                with_depthbuffer=True,
                **pass_kwargs,
            )

            self.renderer.views.link(
                view_name,
                pass_name,
            )

            self.renderer.link_stage(
                source=pass_name,
                target_tags=shadow.receiver_tags,
            )

            self.renderer.attach_pass(
                pass_name=pass_name,
                target_tags=shadow.receiver_tags,
                output="depth",
                uniform=shadow.texture_uniform,
            )

    def _destroy_shadow_resources(
        self,
        shadow: LightShadow,
    ) -> None:
        for pass_name in shadow.pass_names:
            self.renderer.destroy_stage(pass_name)

        for view_name in shadow.view_names:
            self.renderer.views.remove(view_name)

    def _update_shadow_views(
        self,
        light: Light3D,
        shadow: LightShadow,
    ) -> None:
        if shadow.shadow_type == "directional":
            self._update_directional_shadow_view(
                light,
                shadow,
            )
            return

        if shadow.shadow_type == "spot":
            self._update_spot_shadow_view(
                light,
                shadow,
            )
            return

        if shadow.shadow_type == "point":
            self._update_point_shadow_views(
                light,
                shadow,
            )
            return

    def _update_directional_shadow_view(
        self,
        light: Light3D,
        shadow: LightShadow,
    ) -> None:
        if not isinstance(light, DirectionalLight):
            return

        direction = light.direction
        target = shadow.target
        position = target - direction.scale(shadow.distance)

        view = self.renderer.views.get(
            shadow.view_names[0],
        )
        view.position = position
        view.target = target
        view.up = Vector3(0.0, 1.0, 0.0)
        view.near = shadow.near
        view.far = shadow.far
        view.ortho_size = shadow.ortho_size
        view.projection_type = "orthographic"

    def _update_spot_shadow_view(
        self,
        light: Light3D,
        shadow: LightShadow,
    ) -> None:
        if not isinstance(light, SpotLight):
            return

        position = light.world_position
        direction = light.direction

        view = self.renderer.views.get(
            shadow.view_names[0],
        )
        view.position = position
        view.target = position + direction.scale(light.radius)
        view.up = Vector3(0.0, 1.0, 0.0)
        view.near = shadow.near
        view.far = light.radius
        view.fov = light.angle
        view.projection_type = "perspective"

    def _update_point_shadow_views(
        self,
        light: Light3D,
        shadow: LightShadow,
    ) -> None:
        if not isinstance(light, PointLight):
            return

        position = light.world_position

        for index, view_name in enumerate(shadow.view_names):
            direction = self.POINT_FACE_DIRECTIONS[index]
            up = self.POINT_FACE_UPS[index]

            view = self.renderer.views.get(view_name)
            view.position = position
            view.target = position + direction
            view.up = up
            view.near = shadow.near
            view.far = light.radius
            view.fov = 90.0
            view.projection_type = "perspective"

    # =================================== #
    # Culling
    # =================================== #
    def _select_point_light(
        self,
        light: PointLight,
        stage: RenderContext,
        view: View,
    ) -> bool:
        return True

    def _select_spot_light(
        self,
        light: SpotLight,
        stage: RenderContext,
        view: View,
    ) -> bool:
        return True

    # =================================== #
    # Helpers
    # =================================== #
    def _affected_contexts(
        self,
        light: Light3D,
    ) -> list[RenderContext]:
        record = self.registry.get(light.name)

        if record is None:
            return []

        result: list[RenderContext] = []

        for stage in self._contexts():
            stage_tags = getattr(
                stage,
                "tags",
                set(),
            )

            if record.tags and not record.tags.intersection(stage_tags):
                continue

            result.append(stage)

        return result

    def _contexts(self) -> list[RenderContext]:
        return list(
            self.renderer.stages.registry.contexts.values()
        )

    def _get_context(
        self,
        name: str,
    ) -> RenderContext | None:
        try:
            return self.renderer.stages.require_context(name)
        except Exception:
            return None
