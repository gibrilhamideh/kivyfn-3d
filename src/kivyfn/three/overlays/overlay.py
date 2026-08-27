# kivyfn/three/overlays/overlay.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.widget import Widget

from kivyfn.three.math.vector import Vector2, Vector3
from kivyfn.three.views.transform import ViewTransform


if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.render.stage import RenderStage
    from kivyfn.three.types import OverlayAnchor


class Overlay(EventDispatcher):
    name: str = StringProperty("")
    target: Node3D = ObjectProperty()
    widget: Widget = ObjectProperty()
    stage: str = StringProperty("")

    anchor: OverlayAnchor = StringProperty("origin")

    anchor_hint: Vector2 = ObjectProperty(
        Vector2(0.5, 0.5),
    )

    world_offset: Vector3 = ObjectProperty(
        Vector3.zero(),
    )

    screen_offset: Vector2 = ObjectProperty(
        Vector2.zero(),
    )

    hide_when_offscreen: bool = BooleanProperty(True)

    __events__ = (
        "on_dirty",
    )

    def __init__(
        self,
        *,
        name: str,
        target: Node3D,
        widget: Widget,
        stage: str,
        anchor: OverlayAnchor = "origin",
        anchor_hint: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        screen_offset: Vector2 | None = None,
        hide_when_offscreen: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self._anchor_position: Vector3 | None = None

        self.name = name
        self.target = target
        self.widget = widget
        self.stage = stage
        self.anchor = anchor

        self.anchor_hint = (
            Vector2(0.5, 0.5)
            if anchor_hint is None
            else anchor_hint
        )

        self.world_offset = (
            Vector3.zero()
            if world_offset is None
            else world_offset
        )

        self.screen_offset = (
            Vector2.zero()
            if screen_offset is None
            else screen_offset
        )

        self.hide_when_offscreen = hide_when_offscreen

        self.bind(
            target=self._invalidate_anchor,
            anchor=self._invalidate_anchor,
            anchor_hint=self._mark_dirty,
            world_offset=self._mark_dirty,
            screen_offset=self._mark_dirty,
            hide_when_offscreen=self._mark_dirty,
            stage=self._mark_dirty,
        )

        self.widget.bind(
            size=self._mark_dirty,
        )

    def update(
        self,
        stage: RenderStage,
    ) -> None:
        if not self.target.visible_in_tree:
            self.hide()
            return

        local_position = self._resolve_anchor_position()

        world_position = self.target.world_matrix.transform_point(
            local_position,
        )

        world_position += self.world_offset

        screen_position = ViewTransform.world_to_screen(
            stage.viewport.rect,
            stage.view,
            world_position,
        )

        if screen_position is None:
            if self.hide_when_offscreen:
                self.hide()

            return

        x, y, _ = screen_position

        parent = self.widget.parent
        if parent is not None:
            x, y = parent.to_widget(x, y)

        self.show()

        self.widget.x = (
            x
            + self.screen_offset.x
            - self.widget.width * self.anchor_hint.x
        )

        self.widget.y = (
            y
            + self.screen_offset.y
            - self.widget.height * self.anchor_hint.y
        )

    def show(self) -> None:
        self.widget.opacity = 1
        self.widget.disabled = False

    def hide(self) -> None:
        self.widget.opacity = 0
        self.widget.disabled = True

    def _mark_dirty(
        self,
        *_: Any,
    ) -> None:
        self.dispatch("on_dirty")

    def on_dirty(self) -> None:
        pass

    # ======================================== 
    # Helpers
    # ======================================== 
    def _resolve_anchor_position(self) -> Vector3:
        position = self._anchor_position

        if position is None:
            position = self.target.get_anchor_position(
                self.anchor,
            )

            self._anchor_position = position

        return position

    def _invalidate_anchor(
        self,
        *_: Any,
    ) -> None:
        # TODO: Invalidate when target children or geometry change.
        self._anchor_position = None
        self._mark_dirty()
