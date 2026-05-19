# kivyfn/three/scene/interaction.py

from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from typing import Any

from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.scene import Scene
    from kivyfn.three.scene.node import Node3D

@dataclass(slots=True)
class InteractionEvent:
    node: Node3D
    touch: Any
    origin: Vector3
    direction: Vector3
    distance: float | None = None
    point: Vector3 | None = None


class Interaction:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.pressed_node: Node3D | None = None


    def pick(self, touch) -> InteractionEvent | None:
        origin, direction = self.scene.viewport.screen_to_ray(touch.x, touch.y)

        closest = None

        for node in self.scene.root_node.traverse():
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
        if self.pressed_node is None:
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
        if self.pressed_node is None:
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
