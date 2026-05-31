# kivyfn/three/controls/interaction.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from kivy.input.providers.mouse import MouseMotionEvent

from kivyfn.three.controls.base import SceneController
from kivyfn.three.math.vector import Vector3

if TYPE_CHECKING:
    from kivyfn.three.objects.object3d import Object3D
    from kivyfn.three.scene.view import View


@dataclass(slots=True)
class InteractionEvent:
    target: Object3D
    touch: MouseMotionEvent
    origin: Vector3
    direction: Vector3
    distance: float | None = None
    point: Vector3 | None = None
    _propagation_stopped: bool = False

    @property
    def propagation_stopped(self) -> bool:
        return self._propagation_stopped

    def stop_propagation(self) -> None:
        self._propagation_stopped = True

    def __repr__(self) -> str:
        return (
            "InteractionEvent("
            f"target={self.target.name!r}, "
            f"touch=({self.touch.x:.1f}, {self.touch.y:.1f}), "
            f"distance={self.distance}"
            ")"
        )


class InteractionController(SceneController):
    def __init__(
        self,
        view_name: str = "main",
    ) -> None:
        super().__init__()

        self.view_name = view_name
        self.pressed: Object3D | None = None

    def get_view(self) -> View | None:
        if self.scene is None:
            return None

        return self.scene.views.get(self.view_name)

    def make_ray(
        self,
        touch: Any,
    ) -> tuple[Vector3, Vector3] | None:
        if self.scene is None:
            return None

        view = self.get_view()
        if view is None:
            return None

        return self.scene.viewport.screen_to_ray(
            touch.x,
            touch.y,
            view=view,
        )

    def pick(
        self,
        touch: Any,
    ) -> InteractionEvent | None:
        if self.scene is None:
            return None

        ray = self.make_ray(touch)
        if ray is None:
            return None

        origin, direction = ray

        closest: InteractionEvent | None = None

        for object3d in self.scene.root.walk_objects():
            if not object3d.pickable:
                continue

            hit = object3d.intersects_ray(
                origin,
                direction,
            )

            if hit is None:
                continue

            distance, point = hit

            if closest is None or (
                closest.distance is not None
                and distance < closest.distance
            ):
                closest = InteractionEvent(
                    target=object3d,
                    touch=touch,
                    origin=origin,
                    direction=direction,
                    distance=distance,
                    point=point,
                )

        return closest

    def dispatch_interaction(
        self,
        target: Object3D,
        event_name: str,
        event: InteractionEvent,
    ) -> None:
        current = target

        while current is not None:
            current.dispatch(event_name, event)

            if event.propagation_stopped:
                return

            current = current.parent

    def on_touch_down(
        self,
        touch: Any,
    ) -> bool:
        event = self.pick(touch)

        if event is None:
            return False

        self.pressed = event.target

        self.dispatch_interaction(
            event.target,
            "on_press",
            event,
        )

        return True

    def on_touch_move(
        self,
        touch: Any,
    ) -> bool:
        if self.pressed is None:
            return False

        ray = self.make_ray(touch)
        if ray is None:
            return False

        origin, direction = ray

        event = InteractionEvent(
            target=self.pressed,
            touch=touch,
            origin=origin,
            direction=direction,
        )

        self.dispatch_interaction(
            self.pressed,
            "on_drag",
            event,
        )

        return True

    def on_touch_up(
        self,
        touch: Any,
    ) -> bool:
        if self.pressed is None:
            return False

        ray = self.make_ray(touch)
        if ray is None:
            self.pressed = None
            return False

        origin, direction = ray

        event = InteractionEvent(
            target=self.pressed,
            touch=touch,
            origin=origin,
            direction=direction,
        )

        self.dispatch_interaction(
            self.pressed,
            "on_release",
            event,
        )

        self.pressed = None

        return True
