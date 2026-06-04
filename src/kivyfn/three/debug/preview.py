from __future__ import annotations

from functools import partial
from typing import NamedTuple
from collections.abc import Callable

from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget

from kivyfn.three.render.context import RenderPass


class RenderPassPreview(NamedTuple):
    widget: Widget
    render_pass: RenderPass
    color: Color
    rect: Rectangle
    callback: Callable[..., None]


def _sync_preview(
    rect: Rectangle,
    render_pass: RenderPass,
    texture: Texture,
) -> None:
    rect.texture = texture


def create_preview(
    widget: Widget,
    render_pass: RenderPass,
    *,
    pos: tuple[int, int] = (20, 20),
    size: tuple[int, int] = (256, 256),
) -> RenderPassPreview:

    with widget.canvas.after:
        color = Color(1.0, 1.0, 1.0, 1.0)
        rect = Rectangle(
            pos=pos,
            size=size,
            texture=render_pass.texture,
        )

    callback = partial(
        _sync_preview,
        rect,
    )

    render_pass.bind(texture_ref=callback)

    return RenderPassPreview(
        widget=widget,
        render_pass=render_pass,
        color=color,
        rect=rect,
        callback=callback,
    )


def destory_preview(
    preview: RenderPassPreview,
) -> None:
    preview.render_pass.unbind(
        texture_ref=preview.callback,
    )

    preview.widget.canvas.after.remove(preview.color)
    preview.widget.canvas.after.remove(preview.rect)
