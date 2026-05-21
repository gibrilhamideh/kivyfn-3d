# kivyfn/three/controls/interaction.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from kivy.input.providers.mouse import MouseMotionEvent

from kivyfn.three.math.vector import Vector3
from kivyfn.three.controls.base import SceneController

if TYPE_CHECKING:
    from kivyfn.three.scene.node import Node3D


@dataclass(slots=True)
class InteractionEvent:
    node: Node3D
    touch: MouseMotionEvent
    origin: Vector3
    direction: Vector3
    distance: float | None = None
    point: Vector3 | None = None

    def __repr__(self) -> str:
        return (
            "InteractionEvent("
            f"node={self.node.name!r}, "
            f"touch=({self.touch.x:.1f}, {self.touch.y:.1f}), "
            f"distance={self.distance}"
            ")"
        )


class InteractionController(SceneController):
    def __init__(self):
        super().__init__()
        self.pressed_node: Node3D | None = None

    def pick(self, touch: Any) -> InteractionEvent | None:
        if self.scene is None:
            return None

        origin, direction = self.scene.viewport.screen_to_ray(
            touch.x,
            touch.y,
        )

        closest: InteractionEvent | None = None

        for node in self.scene.root.traverse():

            if not node.pickable:
                continue

            hit = getattr(node, "intersects_ray", lambda *_: None)(
                origin,
                direction,
            )

            if hit is None:
                continue

            distance, point = hit

            if closest is None or distance < closest.distance:
                closest = InteractionEvent(
                    node=node,
                    touch=touch,
                    origin=origin,
                    direction=direction,
                    distance=distance,
                    point=point,
                )

        return closest

    def on_touch_down(self, touch) -> bool:
        event = self.pick(touch)

        if event is None:
            return False

        self.pressed_node = event.node
        event.node.dispatch("on_press", event)

        return True

    def on_touch_move(self, touch) -> bool:
        if self.scene is None or self.pressed_node is None:
            return False

        origin, direction = self.scene.viewport.screen_to_ray(
            touch.x,
            touch.y,
        )

        event = InteractionEvent(
            node=self.pressed_node,
            touch=touch,
            origin=origin,
            direction=direction,
        )

        self.pressed_node.dispatch("on_drag", event)

        return True

    def on_touch_up(self, touch) -> bool:
        if self.scene is None or self.pressed_node is None:
            return False

        origin, direction = self.scene.viewport.screen_to_ray(
            touch.x,
            touch.y,
        )

        event = InteractionEvent(
            node=self.pressed_node,
            touch=touch,
            origin=origin,
            direction=direction,
        )

        self.pressed_node.dispatch("on_release", event)
        self.pressed_node = None

        return True
