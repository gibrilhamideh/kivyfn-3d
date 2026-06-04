# kivyfn/three/lights/manager.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kivy.event import EventDispatcher

if TYPE_CHECKING:
    from kivyfn.three.types import SceneObject
    from kivyfn.three.render.renderer import Renderer
    from kivyfn.three.lights.sources.base import Light3D
    from kivyfn.three.lights.template import ShadowConfig


@dataclass(slots=True)
class LightRecord:
    light: Light3D
    shadow_view_name: str | None = None
    shadow_pass_name: str | None = None


class LightManager(EventDispatcher):

    def __init__(
        self,
        renderer: Renderer,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.renderer = renderer
        self.by_light: dict[int, LightRecord] = {}

    def __repr__(self) -> str:
        return (
            "LightManager("
            f"lights={len(self.by_light)}"
            ")"
        )

    # =================================== #
    # Lifecycle
    # =================================== #
    def create(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            self.register(light)

    def destroy(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            self.unregister(light)

    def register(
        self,
        light: Light3D,
    ) -> None:
        light_id = id(light)

        if light_id in self.by_light:
            return

        record = LightRecord(light=light)
        self.by_light[light_id] = record

        light.bind(on_light_dirty=self.queue_light_dirty)

        shadow = light.config.shadow
        if shadow is not None and shadow.enabled:
            self._create_shadow_resources(
                light=light,
                shadow=shadow,
                record=record,
            )

        self.sync_transform(light)
        self.sync_light(light)

    def unregister(
        self,
        light: Light3D,
    ) -> None:
        light_id = id(light)
        record = self.by_light.pop(light_id, None)

        if record is None:
            return

        light.unbind(on_light_dirty=self.queue_light_dirty)

        if record.shadow_pass_name is not None:
            self.renderer.destroy_stage(record.shadow_pass_name)

        if record.shadow_view_name is not None:
            self.renderer.views.remove(record.shadow_view_name)

    # =================================== #
    # Dirty
    # =================================== #
    def queue_light_dirty(
        self,
        light: Light3D,
    ) -> None:
        self.sync_light(light)

    # =================================== #
    # Sync
    # =================================== #
    def sync_transform(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            record = self.by_light.get(id(light))

            if record is None:
                continue

            if record.shadow_view_name is None:
                continue

            view = self.renderer.views.require(record.shadow_view_name)

            position = light.world_position
            target = position + light.world_forward

            view.set_position(position)
            view.set_target(target)

    def sync_visibility(
        self,
        node: SceneObject,
    ) -> None:
        for light in node.walk(filter="lights"):
            self.sync_light(light)

    def sync_light(
        self,
        light: Light3D,
    ) -> None:
        # Later this is where you sync light uniforms into affected stages.
        #
        # For now, shadow resources are already created, and visibility/enabled
        # can control whether the shadow pass is shown.
        record = self.by_light.get(id(light))

        if record is None:
            return

        if record.shadow_pass_name is None:
            return

        if light.enabled and light.visible_in_tree:
            self.renderer.show_stage(record.shadow_pass_name)
        else:
            self.renderer.hide_stage(record.shadow_pass_name)

    # =================================== #
    # Shadow Resources
    # =================================== #
    def _create_shadow_resources(
        self,
        *,
        light: Light3D,
        shadow: ShadowConfig,
        record: LightRecord,
    ) -> None:
        view_config = shadow.view

        view = self.renderer.views.create(
            shadow.view_name,
            position=light.world_position,
            target=light.world_position + light.world_forward,
            projection_type=view_config.projection_type,
            near=view_config.near,
            far=view_config.far,
            ortho_size=view_config.ortho_size,
            fov=view_config.fov,
        )

        shadow_pass = self.renderer.create_pass(
            name=shadow.pass_name,
            view_name=view.name,
            shader=shadow.shader,
            output="depth",
            output_uniform=shadow.texture_uniform,
            tags=set(shadow.caster_tags),
            use_viewport_size=False,
            fbo_width=shadow.resolution,
            fbo_height=shadow.resolution,
            with_depthbuffer=True,
            with_stencilbuffer=False,
            clear_color=True,
            clear_depth=True,
            clear_stencil=False,
        )

        self.renderer.attach_pass(
            pass_name=shadow_pass.name,
            output="depth",
            output_uniform=shadow.texture_uniform,
            target_tags=set(shadow.receiver_tags),
        )

        self.renderer.link_stage(
            source=shadow_pass.name,
            target_tags=set(shadow.receiver_tags),
        )

        record.shadow_view_name = view.name
        record.shadow_pass_name = shadow_pass.name

