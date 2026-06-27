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


class Overlay(EventDispatcher):
    name: str = StringProperty("")
    anchor: Node3D = ObjectProperty()
    widget: Widget = ObjectProperty()
    stage: str = StringProperty("")

    offset: Vector2 = ObjectProperty(Vector2.zero())
    world_offset: Vector3 = ObjectProperty(Vector3.zero())
    hide_when_offscreen: bool = BooleanProperty(True)

    __events__ = (
        "on_dirty",
    )

    def __init__(
        self,
        *,
        name: str,
        anchor: Node3D,
        widget: Widget,
        stage: str,
        offset: Vector2 | None = None,
        world_offset: Vector3 | None = None,
        hide_when_offscreen: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.name = name
        self.anchor = anchor
        self.widget = widget
        self.stage = stage

        self.offset = offset or Vector2.zero()
        self.world_offset = world_offset or Vector3.zero()
        self.hide_when_offscreen = hide_when_offscreen

        self.bind(
            offset=self._mark_dirty,
            world_offset=self._mark_dirty,
            hide_when_offscreen=self._mark_dirty,
            stage=self._mark_dirty,
        )

    def update(
        self,
        stage: RenderStage,
    ) -> None:
        if not self.anchor.visible_in_tree:
            self.hide()
            return

        world_position = self.anchor.world_position + self.world_offset

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

        self.widget.center_x = x + self.offset.x
        self.widget.center_y = y + self.offset.y

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
