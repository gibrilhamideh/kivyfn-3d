
from __future__ import annotations

from typing import TYPE_CHECKING, overload

from kivy.clock import Clock
from kivy.uix.widget import Widget

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

        # Active overlays only.
        self._by_id: dict[int, Overlay] = {}

        # anchor -> overlay name -> overlay id
        self._by_anchor: dict[Node3D, dict[str, int]] = {}

        # stage name -> overlay ids
        self._by_stage: dict[str, set[int]] = {}

        self._queued: set[int] = set()

        self._flush = Clock.create_trigger(
            self.flush,
            -1,
        )

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
                for name, overlay_id in self._by_anchor.get(
                    anchor,
                    {},
                ).items()
                if overlay_id in self._by_id
            }

        assert stage is not None

        return {
            self._by_id[overlay_id]
            for overlay_id in self._by_stage.get(stage, set())
            if overlay_id in self._by_id
        }

    def get(
        self,
        anchor: Node3D,
        name: str,
    ) -> Overlay | None:
        overlay_id = self._by_anchor.get(
            anchor,
            {},
        ).get(name)

        if overlay_id is None:
            return None

        return self._by_id.get(overlay_id)

    def is_active(
        self,
        overlay: Overlay,
    ) -> bool:
        active_overlay = self.get(
            overlay.anchor,
            overlay.name,
        )

        return active_overlay is overlay

    def has_anchor(
        self,
        anchor: Node3D,
    ) -> bool:
        return anchor in self._by_anchor

    def has_stage(
        self,
        stage: str,
    ) -> bool:
        return stage in self._by_stage

    # =================================== #
    # Activation
    # =================================== #
    def activate(
        self,
        overlay: Overlay,
    ) -> None:
        anchor = overlay.anchor
        stage = overlay.stage

        if anchor.scene is not self.scene:
            raise ValueError(
                f"Cannot activate overlay {overlay.name!r}: "
                f"anchor {anchor.name!r} does not belong to this scene."
            )

        self.scene.stages.registry.require(stage)

        by_anchor = self._by_anchor.get(anchor)

        if by_anchor is not None:
            active_overlay_id = by_anchor.get(overlay.name)

            if active_overlay_id == id(overlay):
                return

            if active_overlay_id is not None:
                raise ValueError(
                    f"Another overlay named {overlay.name!r} is already "
                    f"active on node {anchor.name!r}."
                )

        is_new_anchor = by_anchor is None
        is_new_stage = not self.has_stage(stage)

        if by_anchor is None:
            by_anchor = {}
            self._by_anchor[anchor] = by_anchor

        by_stage = self._by_stage.setdefault(
            stage,
            set(),
        )

        if is_new_anchor:
            self.bind_anchor(anchor)

        if is_new_stage:
            self.bind_stage(stage)

        self._add(
            overlay,
            by_anchor,
            by_stage,
        )

    def deactivate(
        self,
        overlay: Overlay,
    ) -> None:
        by_anchor = self._by_anchor.get(
            overlay.anchor,
        )

        if by_anchor is None:
            return

        active_overlay_id = by_anchor.get(
            overlay.name,
        )

        if active_overlay_id != id(overlay):
            return

        self._remove(
            overlay.name,
            by_anchor,
        )

        overlay.hide()

    def deactivate_anchor(
        self,
        anchor: Node3D,
    ) -> None:
        overlay_ids = list(
            self._by_anchor.get(
                anchor,
                {},
            ).values()
        )

        for overlay_id in overlay_ids:
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.deactivate(overlay)

    def deactivate_stage(
        self,
        stage: str,
    ) -> None:
        overlay_ids = list(
            self._by_stage.get(
                stage,
                set(),
            )
        )

        for overlay_id in overlay_ids:
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.deactivate(overlay)

    def remove(self) -> None:
        for overlay in list(self._by_id.values()):
            self.deactivate(overlay)

        self._queued.clear()

    # Kept for existing RenderStage removal code.
    def clear_stage(
        self,
        stage: str,
    ) -> None:
        self.deactivate_stage(stage)

    # =================================== #
    # Binders
    # =================================== #
    def bind_stage(
        self,
        stage: str,
    ) -> None:
        render_stage = self.scene.stages.registry.require(stage)

        render_stage.bind(
            on_view_dirty=self._on_stage_dirty,
            on_viewport_dirty=self._on_stage_dirty,
            on_size_dirty=self._on_stage_dirty,
        )

    def unbind_stage(
        self,
        stage: str,
    ) -> None:
        try:
            render_stage = self.scene.stages.registry.require(stage)
        except (KeyError, ValueError):
            return

        render_stage.unbind(
            on_view_dirty=self._on_stage_dirty,
            on_viewport_dirty=self._on_stage_dirty,
            on_size_dirty=self._on_stage_dirty,
        )

    def bind_anchor(
        self,
        anchor: Node3D,
    ) -> None:
        anchor.bind(
            on_transform_dirty=self._on_anchor_dirty,
            on_visibility_dirty=self._on_anchor_dirty,
        )

    def unbind_anchor(
        self,
        anchor: Node3D,
    ) -> None:
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

    def flush(
        self,
        *_,
    ) -> None:
        queued = tuple(self._queued)
        self._queued.clear()

        for overlay_id in queued:
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            stage = self.scene.stages.registry.get(
                overlay.stage,
            )

            if stage is None:
                overlay.hide()
                continue

            overlay.update(stage)

    # =================================== #
    # Dirty Marking
    # =================================== #
    def mark_anchor_dirty(
        self,
        anchor: Node3D,
    ) -> None:
        for overlay_id in self._by_anchor.get(
            anchor,
            {},
        ).values():
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.queue(overlay)

    def mark_stage_dirty(
        self,
        stage: str,
    ) -> None:
        for overlay_id in self._by_stage.get(
            stage,
            set(),
        ):
            overlay = self._by_id.get(overlay_id)

            if overlay is None:
                continue

            self.queue(overlay)

    def mark_scene_dirty(self) -> None:
        for overlay in tuple(self._by_id.values()):
            self.queue(overlay)

    # =================================== #
    # Dirty Events
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
    # Internal Registration
    # =================================== #
    def _add(
        self,
        overlay: Overlay,
        by_anchor: dict[str, int],
        by_stage: set[int],
    ) -> None:
        overlay_id = id(overlay)

        if overlay_id in self._by_id:
            return

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

        by_stage = self._by_stage.get(
            overlay.stage,
        )

        if by_stage is not None:
            by_stage.discard(overlay_id)

            if not by_stage:
                self.unbind_stage(overlay.stage)
                self._by_stage.pop(
                    overlay.stage,
                    None,
                )

        if not by_anchor:
            self.unbind_anchor(overlay.anchor)
            self._by_anchor.pop(
                overlay.anchor,
                None,
            )

        overlay.unbind(
            on_dirty=self._on_overlay_dirty,
        )

        self._queued.discard(overlay_id)
        self._remove_widget(overlay.widget)

    # =================================== #
    # Widget Management
    # =================================== #
    def _add_widget(
        self,
        widget: Widget,
    ) -> None:
        if widget.parent is self.scene:
            return

        if widget.parent is not None:
            raise ValueError(
                "Cannot activate overlay widget because it already "
                "belongs to another parent."
            )

        self.scene.add_widget(widget)

    def _remove_widget(
        self,
        widget: Widget,
    ) -> None:
        if widget.parent is self.scene:
            self.scene.remove_widget(widget)


