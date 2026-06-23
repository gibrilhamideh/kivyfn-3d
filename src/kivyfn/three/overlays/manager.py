from __future__ import annotations

from typing import TYPE_CHECKING, overload

from kivy.clock import Clock
from kivy.uix.widget import Widget

from kivyfn.three.math.vector import Vector2, Vector3
from kivyfn.three.overlays.overlay import Overlay

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.viewport import Viewport


class OverlayManager:
    def __init__(
        self,
        scene: Scene,
    ) -> None:
        self.scene = scene

        self._by_anchor: dict[Node3D, dict[str, Overlay]] = {}
        self._by_viewport: dict[Viewport, set[Overlay]] = {}
        self._queued: dict[int, Overlay] = {}

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
        viewport: None = None,
    ) -> dict[str, Overlay]:
        ...

    @overload
    def overlays_of(
        self,
        *,
        anchor: None = None,
        viewport: Viewport,
    ) -> set[Overlay]:
        ...

    def overlays_of(
        self,
        *,
        anchor: Node3D | None = None,
        viewport: Viewport | None = None,
    ) -> dict[str, Overlay] | set[Overlay]:
        if anchor is None and viewport is None:
            raise ValueError(
                "overlays_of() requires either 'anchor' or 'viewport'."
            )

        if anchor is not None and viewport is not None:
            raise ValueError(
                "overlays_of() accepts either 'anchor' or 'viewport', not both."
            )

        if anchor is not None:
            return self._by_anchor.get(anchor, {})

        assert viewport is not None
        return self._by_viewport.get(viewport, set())

    def has_viewport(
        self,
        viewport: Viewport,
    ) -> bool:
        return viewport in self._by_viewport

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
        return self.overlays_of(anchor=anchor).get(name)

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

    # =================================== #
    # Attachments
    # =================================== #
    def attach(
        self,
        anchor: Node3D,
        widget: Widget,
        *,
        name: str,
        viewport: Viewport,
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
    ) -> Overlay:

        is_new_anchor = not self.has_anchor(anchor)
        is_new_viewport = not self.has_viewport(viewport)

        by_anchor = self._by_anchor.setdefault(anchor, {})
        by_viewport = self._by_viewport.setdefault(viewport, set())

        if name in by_anchor:
            raise ValueError(
                f"Overlay {name!r} already exists on node {anchor.name!r}."
            )

        if is_new_viewport:
            self.bind_viewport(viewport)

        if is_new_anchor:
            self.bind_anchor(anchor)

        overlay = Overlay(
            name=name,
            anchor=anchor,
            widget=widget,
            viewport=viewport,
            offset=offset or Vector2.zero(),
            world_offset=world_offset or Vector3.zero(),
            hide_when_offscreen=hide_when_offscreen,
        )

        self._add(overlay, by_anchor, by_viewport)
        return overlay

    def detach(
        self,
        anchor: Node3D,
        name: str,
    ) -> None:

        by_anchor = self.overlays_of(anchor=anchor)
        if name not in by_anchor:
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
        for name in list(self.overlays_of(anchor=anchor)):
            self.detach(anchor, name)

    def clear_viewport(
        self,
        viewport: Viewport,
    ) -> None:
        for overlay in list(self.overlays_of(viewport=viewport)):
            self.detach(
                overlay.anchor,
                overlay.name,
            )

    # =================================== #
    # Binders
    # =================================== #
    def bind_viewport(self, viewport: Viewport) -> None:
        viewport.bind(
            on_view_dirty=self._on_viewport_dirty,
            on_viewport_dirty=self._on_viewport_dirty,
        )

    def unbind_viewport(self, viewport: Viewport) -> None:
        viewport.unbind(
            on_view_dirty=self._on_viewport_dirty,
            on_viewport_dirty=self._on_viewport_dirty,
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
        self._queued[id(overlay)] = overlay
        self._flush()


    def flush(self, *_) -> None:
        queued = list(self._queued.values())
        self._queued.clear()

        for overlay in queued:
            overlay.update()

    # =================================== #
    # Dirty Flags
    # =================================== #

    def mark_anchor_dirty(self, anchor: Node3D):
        for overlay in self.overlays_of(anchor=anchor).values():
            self.queue(overlay)

    def mark_viewport_dirty(self, viewport: Viewport) -> None:
        for overlay in self.overlays_of(viewport=viewport):
            self.queue(overlay)

    def mark_scene_dirty(self) -> None:
        for overlays in self._by_anchor.values():
            for overlay in overlays.values():
                self.queue(overlay)

    # =================================== #
    # Dirty events
    # =================================== #
    def _on_anchor_dirty(
        self,
        anchor: Node3D,
    ) -> None:
        self.mark_anchor_dirty(anchor)

    def _on_viewport_dirty(
        self,
        viewport: Viewport,
    ) -> None:
        self.mark_viewport_dirty(viewport)


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
        by_anchor: dict[str, Overlay],
        by_viewport: set,
    ) -> None:
        name = overlay.name
        widget = overlay.widget

        by_anchor[name] = overlay
        by_viewport.add(overlay)

        self._add_widget(widget)
        self.queue(overlay)

    def _remove(
        self,
        name: str,
        by_anchor: dict[str, Overlay]
    ) -> None:

        overlay = by_anchor.pop(name)
        by_viewport = self.overlays_of(viewport=overlay.viewport)

        by_viewport.discard(overlay)
        if not by_viewport:
            self.unbind_viewport(overlay.viewport)
            self._by_viewport.pop(overlay.viewport)

        if not by_anchor:
            self.unbind_anchor(overlay.anchor)
            self._by_anchor.pop(overlay.anchor)

        self._queued.pop(id(overlay), None)
        self._remove_widget(overlay.widget)

