from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from functools import partial
from collections.abc import Callable

from kivy.clock import Clock, ClockEvent
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture

from kivyfn.three.types import RenderPassName

if TYPE_CHECKING:
    from kivyfn.three import Scene
    from kivyfn.three.render.context import RenderPass

@dataclass(slots=True)
class RenderPassPreview:
    name: RenderPassName
    color: Color
    rect: Rectangle
    callback: Callable[..., None]


@dataclass(slots=True)
class FpsDisplay:
    color: Color
    rect: Rectangle
    label: Label
    event: ClockEvent


class SceneTools:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene

        self._previews: list[RenderPassPreview] = []
        self._fps_display: FpsDisplay | None = None

    # =================================== #
    # Preview
    # =================================== #
    def display_preview(
        self,
        stage: RenderPassName,
        *,
        pos: tuple[int, int] = (20, 20),
        size: tuple[int, int] = (256, 256),
    ) -> None:

        def tick(*_):

            ctx = self.scene.stages.registry.require_pass(stage)
            with self.scene.canvas.after:
                color = Color(1.0, 1.0, 1.0, 1.0)
                rect = Rectangle(
                    pos=pos,
                    size=size,
                    texture=ctx.texture,
                )

            callback = partial(
                self._sync_preview,
                rect,
            )

            ctx.bind(texture_ref=callback)

            preview = RenderPassPreview(
                name=stage,
                color=color,
                rect=rect,
                callback=callback,
            )

            self._previews.append(preview)

        Clock.schedule_once(tick, -1)

    def remove_preview(
        self,
        preview: RenderPassPreview,
    ) -> None:
        ctx = self.scene.stages.registry.require_pass(preview.name)
        ctx.unbind(
            texture_ref=preview.callback,
        )

        self._remove_instruction(preview.color)
        self._remove_instruction(preview.rect)

        if preview in self._previews:
            self._previews.remove(preview)

    def clear_previews(self) -> None:
        for preview in self._previews[:]:
            self.remove_preview(preview)

    def _sync_preview(
        self,
        rect: Rectangle,
        render_pass: RenderPass,
        texture: Texture,
    ) -> None:
        rect.texture = texture

    # =================================== #
    # FPS / Frame Time
    # =================================== #
    def display_fps(
        self,
        *,
        pos: tuple[int, int] = (20, 20),
        font_size: int = 16,
        interval: float = 1.0,
    ) -> FpsDisplay:
        if self._fps_display is not None:
            return self._fps_display

        label = Label(
            text="FPS: --\nFrame: -- ms",
            font_size=font_size,
            size_hint=(None, None),
        )

        label.texture_update()
        label.width = label.texture_size[0]
        label.height = label.texture_size[1]

        with self.scene.canvas.after:
            color = Color(1.0, 1.0, 1.0, 1.0)
            rect = Rectangle(
                pos=pos,
                size=label.size,
                texture=label.texture,
            )

        event = Clock.schedule_interval(
            partial(self._update_fps_display, label, rect),
            interval,
        )

        display = FpsDisplay(
            color=color,
            rect=rect,
            label=label,
            event=event,
        )

        self._fps_display = display

        return display

    def remove_fps(self) -> None:
        if self._fps_display is None:
            return

        self._fps_display.event.cancel()
        self._remove_instruction(self._fps_display.color)
        self._remove_instruction(self._fps_display.rect)

        self._fps_display = None

    def _update_fps_display(
        self,
        label: Label,
        rect: Rectangle,
        dt: float,
    ) -> None:
        frame_ms = Clock.frametime * 1000.0

        label.text = (
            f"FPS: {Clock.get_fps():.1f}\n"
            f"Frame: {frame_ms:.2f} ms"
        )

        label.texture_update()
        rect.texture = label.texture
        rect.size = label.size

    # =================================== #
    # Cleanup
    # =================================== #
    def clear(self) -> None:
        self.clear_previews()
        self.remove_fps()

    def _remove_instruction(
        self,
        instruction,
    ) -> None:
        canvas = self.scene.canvas.after

        if instruction in canvas.children:
            canvas.remove(instruction)
