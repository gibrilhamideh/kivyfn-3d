from __future__ import annotations

from typing import TYPE_CHECKING, overload

from kivy.clock import Clock
from kivy.uix.widget import Widget

from kivyfn.three.math.vector import Vector2, Vector3
from kivyfn.three.overlays.overlay import Overlay

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.render.stage import RenderStage
    from kivyfn.three.scene.scene import Scene


class OverlayManager:
    def __init__(
        self,
        scene: Scene,
    ) -> None:
        self.scene = scene

        self._by_id: dict[int, Overlay] = {}

        self._by_anchor: dict[Node3D, dict[str, int]] = {}
        self._by_stage: dict[str, set[int]] = {}

        self._queued: set[int] = set()

        self._flush = Clock.create_trigger(self.flush, -1)

        self.scene.bind(
            pos=self._on_scene_dirty,
            size=self._on_scene_dirty,
        )

    # =================================== #
    # Lookup
    # =================================== #
    @overload
    def overlays_of(
        self,
        *,
        anchor: Node3D,
        stage: None = None,
    ) -> dict[str, Overlay]:
        ...

    @overload
    def overlays_of(
        self,
        *,
        anchor: None = None,
        stage: str,
    ) -> set[Overlay]:
        ...

    def overlays_of(
        self,
        *,
        anchor: Node3D | None = None,
        stage: str | None = None,
    ) -> dict[str, Overlay] | set[Overlay]:
        if anchor is None and stage is None:
            raise ValueError(
                "overlays_of() requires either 'anchor' or 'stage'."
            )

        if anchor is not None and stage is not None:
            raise ValueError(
                "overlays_of() accepts either 'anchor' or 'stage', not both."
            )

        if anchor is not None:
            return {
                name: self._by_id[overlay_id]
                for name, overlay_id in self._by_anchor.get(anchor, {}).items()
                if overlay_id in self._by_id
            }

        assert stage is not None
        return {
            self._by_id[overlay_id]
            for overlay_id in self._by_stage.get(stage, set())
            if overlay_id in self._by_id
        }

    def has_stage(
        self,
        stage: str,
    ) -> bool:
        return stage in self._by_stage

    def has_anchor(
        self,
        anchor: Node3D,
    ) -> bool:
        return anchor in self._by_anchor

    def get(
        self,
        anchor: Node3D,
        name: str,
    ) -> Overlay | None:
        overlay_id = self._by_anchor.get(anchor, {}).get(name)

        if overlay_id is None:
            return None

        return self._by_id.get(overlay_id)


    # =================================== #
    # Attachments
    # =================================== #
    def attach(
        self,
        anchor: Node3D,
        widget: Widget,
        *,
        name: str,
        stage: str,
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
    ) -> Overlay:

        self.scene.stages.registry.require(stage)

        by_anchor = self._by_anchor.get(anchor)

        if by_anchor is not None and name in by_anchor:
            raise ValueError(
                f"Overlay {name!r} already exists on node {anchor.name!r}."
            )

        is_new_anchor = by_anchor is None
        is_new_stage = not self.has_stage(stage)

        if by_anchor is None:
            by_anchor = {}
            self._by_anchor[anchor] = by_anchor

        by_stage = self._by_stage.setdefault(stage, set())

        if is_new_stage:
            self.bind_stage(stage)

        if is_new_anchor:
            self.bind_anchor(anchor)

        overlay = Overlay(
            name=name,
            anchor=anchor,
            widget=widget,
            stage=stage,
            offset=offset or Vector2.zero(),
            world_offset=world_offset or Vector3.zero(),
            hide_when_offscreen=hide_when_offscreen,
        )

        self._add(overlay, by_anchor, by_stage)
        return overlay

    def detach(
        self,
        anchor: Node3D,
        name: str,
    ) -> None:

        by_anchor = self._by_anchor.get(anchor)

        if by_anchor is None or name not in by_anchor:
            raise ValueError(
                f"Overlay {name!r} does not exist on node {anchor.name!r}."
            )

        self._remove(name, by_anchor)

    def remove(self) -> None:
        for anchor in list(self._by_anchor):
            self.clear_anchor(anchor)

        self._queued.clear()

    def clear_anchor(
        self,
        anchor: Node3D,
    ) -> None:
        for name in list(self._by_anchor.get(anchor, {})):
            self.detach(anchor, name)

    def clear_stage(
        self,
        stage: str,
    ) -> None:
        for overlay_id in list(self._by_stage.get(stage, set())):
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.detach(
                overlay.anchor,
                overlay.name,
            )

    # =================================== #
    # Binders
    # =================================== #
    def bind_stage(self, stage: str) -> None:
        render_stage = self.scene.stages.registry.require(stage)

        render_stage.bind(
            on_view_dirty=self._on_stage_dirty,
            on_viewport_dirty=self._on_stage_dirty,
            on_size_dirty=self._on_stage_dirty,
        )

    def unbind_stage(self, stage: str) -> None:
        try:
            render_stage = self.scene.stages.registry.require(stage)
        except (KeyError, ValueError):
            return

        render_stage.unbind(
            on_view_dirty=self._on_stage_dirty,
            on_viewport_dirty=self._on_stage_dirty,
            on_size_dirty=self._on_stage_dirty,
        )

    def bind_anchor(self, anchor: Node3D) -> None:
        anchor.bind(
            on_transform_dirty=self._on_anchor_dirty,
            on_visibility_dirty=self._on_anchor_dirty,
        )

    def unbind_anchor(self, anchor: Node3D) -> None:
        anchor.unbind(
            on_transform_dirty=self._on_anchor_dirty,
            on_visibility_dirty=self._on_anchor_dirty,
        )

    # =================================== #
    # Updates
    # =================================== #
    def queue(
        self,
        overlay: Overlay,
    ) -> None:
        overlay_id = id(overlay)

        if overlay_id not in self._by_id:
            return

        self._queued.add(overlay_id)
        self._flush()

    def flush(self, *_) -> None:
        queued = list(self._queued)
        self._queued.clear()

        for overlay_id in queued:
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            stage = self.scene.stages.registry.get(overlay.stage)

            if stage is None:
                overlay.hide()
                continue

            overlay.update(stage)

    # =================================== #
    # Dirty Flags
    # =================================== #

    def mark_anchor_dirty(self, anchor: Node3D) -> None:
        for overlay_id in self._by_anchor.get(anchor, {}).values():
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.queue(overlay)

    def mark_stage_dirty(self, stage: str) -> None:
        for overlay_id in self._by_stage.get(stage, set()):
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.queue(overlay)

    def mark_scene_dirty(self) -> None:
        for overlay in list(self._by_id.values()):
            self.queue(overlay)

    # =================================== #
    # Dirty events
    # =================================== #
    def _on_anchor_dirty(
        self,
        anchor: Node3D,
    ) -> None:
        self.mark_anchor_dirty(anchor)

    def _on_stage_dirty(
        self,
        stage: RenderStage,
        *_,
    ) -> None:
        self.mark_stage_dirty(stage.name)

    def _on_overlay_dirty(
        self,
        overlay: Overlay,
    ) -> None:
        self.queue(overlay)

    def _on_scene_dirty(
        self,
        *_,
    ) -> None:
        self.mark_scene_dirty()

    # =================================== #
    # Helpers
    # =================================== #
    def _remove_widget(self, widget: Widget) -> None:
        self.scene.remove_widget(widget)

    def _add_widget(self, widget: Widget) -> None:
        self.scene.add_widget(widget)

    def _add(
        self,
        overlay: Overlay,
        by_anchor: dict[str, int],
        by_stage: set[int],
    ) -> None:
        overlay_id = id(overlay)

        self._by_id[overlay_id] = overlay

        by_anchor[overlay.name] = overlay_id
        by_stage.add(overlay_id)

        overlay.bind(
            on_dirty=self._on_overlay_dirty,
        )

        self._add_widget(overlay.widget)
        self.queue(overlay)

    def _remove(
        self,
        name: str,
        by_anchor: dict[str, int],
    ) -> None:

        overlay_id = by_anchor.pop(name)
        overlay = self._by_id.pop(overlay_id)

        by_stage = self._by_stage.get(overlay.stage)

        if by_stage is not None:
            by_stage.discard(overlay_id)

            if not by_stage:
                self.unbind_stage(overlay.stage)
                self._by_stage.pop(overlay.stage, None)

        if not by_anchor:
            self.unbind_anchor(overlay.anchor)
            self._by_anchor.pop(overlay.anchor, None)

        overlay.unbind(
            on_dirty=self._on_overlay_dirty,
        )

        self._queued.discard(overlay_id)
        self._remove_widget(overlay.widget)

