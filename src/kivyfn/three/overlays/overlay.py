# kivyfn/three/attachments/attachment.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from kivy.uix.widget import Widget

from kivyfn.three.math.vector import Vector2, Vector3

if TYPE_CHECKING:
    from kivyfn.three.graph.node import Node3D
    from kivyfn.three.scene.scene import Scene


@dataclass
class Overlay:
    scene: Scene
    anchor: Node3D
    widget: Widget

    view_name: str
    offset: Vector2 = field(default_factory=Vector2.zero)
    world_offset: Vector3 = field(default_factory=Vector3.zero)
    hide_when_offscreen: bool = True

    def update(self) -> None:
        if not self.anchor.visible_in_tree:
            self.hide()
            return

        view = self.scene.views.require(self.view_name)

        world_position = (
            self.anchor.world_position +
            self.world_offset
        )

        screen_position = self.scene.viewport.world_to_screen(
            world_position,
            view=view,
        )

        if screen_position is None:
            if self.hide_when_offscreen:
                self.hide()
            return

        x, y, _z = screen_position

        self.show()
        self.widget.center_x = x + self.offset.x
        self.widget.center_y = y + self.offset.y

    def show(self) -> None:
        self.widget.opacity = 1
        self.widget.disabled = False

    def hide(self) -> None:
        self.widget.opacity = 0
        self.widget.disabled = True

