from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.clock import Clock
from kivy.uix.widget import Widget

from kivyfn.three.math.vector import Vector2, Vector3
from kivyfn.three.overlays.overlay import Overlay

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.scene.scene import Scene


class OverlayManager:
    def __init__(
        self,
        scene: Scene,
        *,
        layer: Widget | None = None,
    ) -> None:
        self.scene = scene
        self.layer = layer or scene

        self._overlays_by_anchor: dict[Node3D, dict[str, Overlay]] = {}
        self._overlays_by_view: dict[str, set[Overlay]] = {}

        self._queued_overlays: dict[int, Overlay] = {}
        self._trigger_flush = Clock.create_trigger(self.flush, -1)

        self.scene.bind(
            pos=self._on_viewport_dirty,
            size=self._on_viewport_dirty,
        )

        # self.scene.views.bind(
        #     on_view_dirty=self._on_view_dirty,
        # )

    # =================================== #
    # Helpers
    # =================================== #
    def get(
        self,
        anchor: Node3D,
        name: str,
    ) -> Overlay | None:
        return self._overlays_by_anchor.get(anchor, {}).get(name)

    def require(
        self,
        anchor: Node3D,
        name: str,
    ) -> Overlay:
        overlay = self.get(anchor, name)

        if overlay is None:
            raise ValueError(
                f"Overlay {name!r} not found on node {anchor.name!r}."
            )

        return overlay

    def overlays_of(
        self,
        anchor: Node3D,
    ) -> list[Overlay]:
        return list(self._overlays_by_anchor.get(anchor, {}).values())

    # =================================== #
    # Attachments
    # =================================== #
    def attach(
        self,
        anchor: Node3D,
        widget: Widget,
        *,
        name: str,
        view_name: str,
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
    ) -> Overlay:
        overlays = self._overlays_by_anchor.setdefault(anchor, {})

        if name in overlays:
            raise ValueError(
                f"Overlay {name!r} already exists on node {anchor.name!r}."
            )

        overlay = Overlay(
            scene=self.scene,
            anchor=anchor,
            widget=widget,
            view_name=view_name,
            offset=offset or Vector2.zero(),
            world_offset=world_offset or Vector3.zero(),
            hide_when_offscreen=hide_when_offscreen,
        )

        overlays[name] = overlay
        self._overlays_by_view.setdefault(view_name, set()).add(overlay)

        if len(overlays) == 1:
            anchor.bind(
                on_transform_dirty=self._on_anchor_dirty,
                on_visibility_dirty=self._on_anchor_dirty,
            )

        self.layer.add_widget(widget)
        self.queue(overlay)

        return overlay

    def detach(
        self,
        anchor: Node3D,
        name: str = "default",
    ) -> None:
        overlays = self._overlays_by_anchor.get(anchor)

        if overlays is None:
            return

        overlay = overlays.pop(name, None)

        if overlay is None:
            return

        self._dequeue(overlay)
        self._remove_from_view(overlay)
        
        widget = overlay.widget
        parent = widget.parent
        if parent is not None:
            parent.remove_widget(widget)

        if not overlays:
            self._overlays_by_anchor.pop(anchor, None)

            anchor.unbind(
                on_transform_dirty=self._on_anchor_dirty,
                on_visibility_dirty=self._on_anchor_dirty,
            )

    def clear(
        self,
        anchor: Node3D,
    ) -> None:
        overlays = self._overlays_by_anchor.get(anchor)

        if overlays is None:
            return

        for name in list(overlays):
            self.detach(anchor, name)

    def clear_all(self) -> None:
        for anchor in list(self._overlays_by_anchor):
            self.clear(anchor)

    # =================================== #
    # Updates
    # =================================== #
    def queue(self, overlay: Overlay) -> None:
        if not self._contains(overlay):
            return

        self._queued_overlays[id(overlay)] = overlay
        self._trigger_flush()

    def update(self, *, force: bool = False) -> None:
        if force:
            for overlays in self._overlays_by_anchor.values():
                for overlay in overlays.values():
                    overlay.update()
            return

        self.flush()

    def flush(self, *_) -> None:
        queued = list(self._queued_overlays.values())
        self._queued_overlays.clear()

        for overlay in queued:
            if self._contains(overlay):
                overlay.update()

    def update_view(self, view_name: str) -> None:
        for overlay in self._overlays_by_view.get(view_name, set()):
            self.queue(overlay)


    # =================================== #
    # Internal
    # =================================== #
    def _contains(self, overlay: Overlay) -> bool:
        overlays = self._overlays_by_anchor.get(overlay.anchor)

        if overlays is None:
            return False

        return overlay in overlays.values()

    def _dequeue(self, overlay: Overlay) -> None:
        self._queued_overlays.pop(id(overlay), None)

    def _remove_from_view(self, overlay: Overlay) -> None:
        view_items = self._overlays_by_view.get(overlay.view_name)

        if view_items is None:
            return

        view_items.discard(overlay)

        if not view_items:
            self._overlays_by_view.pop(overlay.view_name, None)


    # =================================== #
    # Dirty Flags
    # =================================== #
    def _on_anchor_dirty(self, anchor: Node3D, *_) -> None:
        for overlay in self.overlays_of(anchor):
            self.queue(overlay)

    def _on_view_dirty(self, _view_manager, view, _stage_name) -> None:
        self.update_view(view.name)

    def _on_viewport_dirty(self, *_) -> None:
        for overlays in self._overlays_by_anchor.values():
            for overlay in overlays.values():
                self.queue(overlay)
