# kivyfn/three/controls/interaction.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from kivy.input.providers.mouse import MouseMotionEvent

from kivyfn.three.math.vector import Vector3
from kivyfn.three.controls.base import BaseController
from kivyfn.three.views.transform import ViewTransform

if TYPE_CHECKING:
    from kivyfn.three.assets.object3d import Object3D
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.render.stage import RenderStage


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


class BasePicker:
    def __init__(
        self,
        stage_name: str,
    ) -> None:
        self.scene: Scene | None = None
        self.stage_name = stage_name

    def attach(
        self,
        scene: Scene,
    ) -> None:
        self.scene = scene

    def detach(self) -> None:
        self.scene = None

    # =================================== #
    # Stage
    # =================================== #

    def require_scene(self) -> Scene:
        if self.scene is None:
            raise RuntimeError(
                f"{type(self).__name__} is not attached to a scene."
            )

        return self.scene

    def require_stage(self) -> RenderStage:
        scene = self.require_scene()

        return scene.renderer.stages.registry.require(
            self.stage_name,
        )

    # =================================== #
    # Coordinates
    # =================================== #

    def touch_inside_viewport(
        self,
        touch: Any,
    ) -> bool:
        stage = self.require_stage()
        rect = stage.viewport.rect

        return (
            rect.x <= touch.x < rect.x + rect.width
            and rect.y <= touch.y < rect.y + rect.height
        )

    def touch_to_viewport_pixel(
        self,
        touch: Any,
    ) -> tuple[int, int] | None:
        if not self.touch_inside_viewport(touch):
            return None

        stage = self.require_stage()
        rect = stage.viewport.rect

        return (
            int(touch.x - rect.x),
            int(touch.y - rect.y),
        )

    def make_ray(
        self,
        touch: Any,
    ) -> tuple[Vector3, Vector3] | None:
        if not self.touch_inside_viewport(touch):
            return None

        stage = self.require_stage()
        rect = stage.viewport.rect

        return ViewTransform.screen_to_ray(
            rect,
            stage.view,
            touch.x,
            touch.y,
        )

    # =================================== #
    # Pick
    # =================================== #

    def pick(
        self,
        touch: MouseMotionEvent,
    ) -> InteractionEvent | None:
        raise NotImplementedError


class RaycastPicker(BasePicker):
    def pick(
        self,
        touch: Any,
    ) -> InteractionEvent | None:
        scene = self.require_scene()

        ray = self.make_ray(touch)
        if ray is None:
            return None

        origin, direction = ray
        closest: InteractionEvent | None = None

        for object3d in scene.root.walk(filter="objects"):
            if not object3d.pickable:
                continue

            if not object3d.visible_in_tree:
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


class RenderIdPicker(BasePicker):
    def pick(
        self,
        touch: MouseMotionEvent,
    ) -> InteractionEvent | None:
        scene = self.require_scene()

        ray = self.make_ray(touch)
        if ray is None:
            return None

        render_id = self.read_render_id(touch)
        if render_id is None:
            return None

        object3d = scene.registry.get_by_render_id(render_id)
        if object3d is None:
            return None

        if not object3d.pickable:
            return None

        origin, direction = ray

        return InteractionEvent(
            target=object3d,
            touch=touch,
            origin=origin,
            direction=direction,
        )

    def read_render_id(
        self,
        touch: MouseMotionEvent,
    ) -> int | None:
        stage = self.require_stage()
        target = stage.require_target("texture-2d")

        pixel = self.touch_to_viewport_pixel(touch)
        if pixel is None:
            return None

        x, y = pixel

        r, g, b, _ = target.get_pixel_color(
            x,
            y,
        )

        render_id = (r << 16) | (g << 8) | b
        if render_id == 0:
            return None

        return render_id


class InteractionController(BaseController):
    def __init__(
        self,
        picker: RaycastPicker | RenderIdPicker,
    ) -> None:
        super().__init__()

        self.picker = picker
        self.pressed: Object3D | None = None

    def attach(
        self,
        scene: Scene,
    ) -> None:
        super().attach(scene)
        self.picker.attach(scene)

    def detach(self) -> None:
        self.picker.detach()
        super().detach()

    def make_ray(
        self,
        touch: Any,
    ) -> tuple[Vector3, Vector3] | None:
        return self.picker.make_ray(touch)

    def pick(
        self,
        touch: Any,
    ) -> InteractionEvent | None:
        return self.picker.pick(touch)

    def dispatch_interaction(
        self,
        target: Object3D,
        event_name: str,
        event: InteractionEvent,
    ) -> None:
        current = target

        while current is not None:
            current.dispatch(
                event_name,
                event,
            )

            if event.propagation_stopped:
                return

            current = current.parent

    def on_touch_down(
        self,
        touch: MouseMotionEvent,
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
        touch: MouseMotionEvent,
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
        touch: MouseMotionEvent,
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
