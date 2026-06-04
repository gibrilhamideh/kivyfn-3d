# kivyfn/three/controls/base.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.input.providers.mouse import MouseMotionEvent

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene


class BaseController:
    def __init__(self):
        self.scene: Scene | None = None

    def attach(self, scene: Scene) -> None:
        self.scene = scene

    def detach(self) -> None:
        self.scene = None

    def on_touch_down(self, touch: MouseMotionEvent) -> bool:
        return False

    def on_touch_move(self, touch: MouseMotionEvent) -> bool:
        return False

    def on_touch_up(self, touch: MouseMotionEvent) -> bool:
        return False
