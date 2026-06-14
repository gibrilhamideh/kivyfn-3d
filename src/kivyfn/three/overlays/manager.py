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
    ):
        self.scene = scene
        self.layer = layer or scene

        self._overlays: list[Overlay] = []
        self._overlays_by_widget: dict[Widget, Overlay] = {}
        self._overlays_by_anchor: dict[Node3D, list[Overlay]] = {}
        self._overlays_by_view: dict[str, list[Overlay]] = {}

        self._queue: set[int] = set()
        self._queued_overlays: dict[int, Overlay] = {}
        self._trigger_flush = Clock.create_trigger(self.flush, -1)

        self.scene.bind(
            pos=self._on_viewport_dirty,
            size=self._on_viewport_dirty,
        )

        self.scene.views.bind(
            on_view_dirty=self._on_view_dirty,
        )

    def attach(
        self,
        anchor: Node3D,
        widget: Widget,
        *,
        view_name: str = "main",
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
    ) -> Overlay:
        if widget in self._overlays_by_widget:
            raise ValueError("Widget is already attached to an overlay.")

        overlay = Overlay(
            scene=self.scene,
            anchor=anchor,
            widget=widget,
            view_name=view_name,
            offset=offset or Vector2.zero(),
            world_offset=world_offset or Vector3.zero(),
            hide_when_offscreen=hide_when_offscreen,
        )

        self._overlays.append(overlay)
        self._overlays_by_widget[widget] = overlay
        self._overlays_by_anchor.setdefault(anchor, []).append(overlay)
        self._overlays_by_view.setdefault(view_name, []).append(overlay)

        anchor.bind(
            on_transform_dirty=self._on_anchor_dirty,
            on_visibility_dirty=self._on_anchor_dirty,
        )

        self.layer.add_widget(widget)
        self.queue(overlay)

        return overlay

    def detach(self, overlay: Overlay) -> None:
        if overlay not in self._overlays:
            return

        self._dequeue(overlay)

        self._overlays.remove(overlay)
        self._overlays_by_widget.pop(overlay.widget, None)

        anchor_items = self._overlays_by_anchor.get(overlay.anchor)

        if anchor_items is not None:
            if overlay in anchor_items:
                anchor_items.remove(overlay)

            if not anchor_items:
                self._overlays_by_anchor.pop(overlay.anchor, None)

                overlay.anchor.unbind(
                    on_transform_dirty=self._on_anchor_dirty,
                    on_visibility_dirty=self._on_anchor_dirty,
                )

        view_items = self._overlays_by_view.get(overlay.view_name)

        if view_items is not None:
            if overlay in view_items:
                view_items.remove(overlay)

            if not view_items:
                self._overlays_by_view.pop(overlay.view_name, None)

        overlay.destroy()

    def detach_by_widget(self, widget: Widget) -> None:
        overlay = self._overlays_by_widget.get(widget)

        if overlay is not None:
            self.detach(overlay)

    def detach_by_anchor(self, anchor: Node3D) -> None:
        for overlay in list(self._overlays_by_anchor.get(anchor, [])):
            self.detach(overlay)

    def detach_by_subtree(self, root: Node3D) -> None:
        for node in list(root.walk(filter="all")):
            self.detach_by_anchor(node)

    def clear(self) -> None:
        for overlay in list(self._overlays):
            self.detach(overlay)

    def queue(self, overlay: Overlay) -> None:
        if overlay not in self._overlays:
            return

        key = id(overlay)
        self._queue.add(key)
        self._queued_overlays[key] = overlay
        self._trigger_flush()

    def update(self, *, force: bool = False) -> None:
        if force:
            for overlay in self._overlays:
                overlay.update()
            return

        self.flush()

    def flush(self, *_) -> None:
        while self._queue:
            key = self._queue.pop()
            overlay = self._queued_overlays.pop(key, None)

            if overlay is not None and overlay in self._overlays:
                overlay.update()

    def update_view(self, view_name: str) -> None:
        for overlay in self._overlays_by_view.get(view_name, []):
            self.queue(overlay)

    def destroy(self) -> None:
        self.clear()
        self._queue.clear()
        self._queued_overlays.clear()
        self._trigger_flush.cancel()

        self.scene.unbind(
            pos=self._on_viewport_dirty,
            size=self._on_viewport_dirty,
        )

        self.scene.views.unbind(
            on_view_dirty=self._on_view_dirty,
        )

    def _dequeue(self, overlay: Overlay) -> None:
        key = id(overlay)
        self._queue.discard(key)
        self._queued_overlays.pop(key, None)

    def _on_anchor_dirty(self, anchor: Node3D, *_):
        for overlay in self._overlays_by_anchor.get(anchor, []):
            self.queue(overlay)

    def _on_view_dirty(self, _view_manager, view, _stage_name):
        self.update_view(view.name)

    def _on_viewport_dirty(self, *_):
        for overlay in self._overlays:
            self.queue(overlay)
