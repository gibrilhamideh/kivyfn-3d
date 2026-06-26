# kivyfn/three/graphics/gl/fbo.py

from __future__ import annotations

from typing import Any
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from kivy.graphics import Callback, Instruction, InstructionGroup
from kivy.graphics import RenderContext as KivyRenderContext

from kivyfn.three.views.view import View
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.bind import BindTexture
from kivyfn.three.graphics.gl.texture import Texture2D, TextureCube


@dataclass(frozen=True, slots=True)
class RenderFrame:
    begin: Callable[..., None]
    end: Callable[..., None]
    apply: Callable[..., None] | None = None


class BaseTargetContext(KivyRenderContext):

    texture_group: InstructionGroup
    render_group: InstructionGroup

    def __init__(
        self,
        view: View,
        viewport: Viewport,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.view = view
        self.viewport = viewport

        self.texture_group = InstructionGroup()
        self.render_group = InstructionGroup()

        self._uniforms: dict[str, Any] = {}
        self._bind_events()


    # =================================== #
    # Bind Events
    # =================================== #
    #
    def _bind_events(self) -> None:
        self.view.bind(on_dirty=self.sync_view)
        self.viewport.bind(on_dirty=self.sync_view)

    # =================================== #
    # Build Helpers
    # =================================== #
    def build(
        self,
        frames: RenderFrame | Iterable[RenderFrame],
        *,
        sync_view: bool = True,
    ) -> None:
        super().clear()

        if isinstance(frames, RenderFrame):
            frames = (frames,)

        for frame in frames:
            super().add(Callback(frame.begin))

            if frame.apply is not None:
                super().add(Callback(frame.apply))

            super().add(self.texture_group)
            super().add(self.render_group)
            super().add(Callback(frame.end))

        if sync_view:
            self.sync_view()

        self.ask_update()

    # =================================== #
    # Depth Test
    # =================================== #
    def enable_depthtest(
        self,
        *_: Any,
    ) -> None:
        GL.enable(GL.DEPTH_TEST)

    def disable_depthtest(
        self,
        *_: Any,
    ) -> None:
        GL.disable(GL.DEPTH_TEST)

    # =================================== #
    # Groups
    # =================================== #

    def add(
        self,
        c: Instruction,
    ) -> None:
        self.render_group.add(c)
        self.ask_update()

    def remove(
        self,
        c: Instruction,
    ) -> None:
        self.render_group.remove(c)
        self.ask_update()

    def clear(
        self,
    ) -> None:
        self.render_group.clear()
        self.ask_update()

    def clear_textures(
        self,
    ) -> None:
        self.texture_group.clear()
        self.ask_update()

    def clear_all(
        self,
    ) -> None:
        self.texture_group.clear()
        self.render_group.clear()
        self.ask_update()

    # =================================== #
    # Uniforms
    # =================================== #
    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self._uniforms[name] = value

        if isinstance(value, list):
            self[name] = value.copy()
        else:
            self[name] = value

        self.ask_update()

    def sync_uniforms(self) -> None:
        for key, value in list(self._uniforms.items()):
            self.apply_uniform(
                key,
                value,
            )

    @property
    def uniforms(self) -> dict[str, Any]:
        return self._uniforms


    # =================================== #
    # BindTexutre
    # =================================== #
    def bind_texture(
        self,
        *,
        uniform: str,
        texture: Texture2D | TextureCube,
        slot: int,
    ) -> BindTexture:
        instruction = BindTexture(
            stage=self,
            uniform=uniform,
            texture=texture,
            slot=slot,
        )

        self.texture_group.add(instruction)

        self.apply_uniform(
            uniform,
            slot,
        )

        return instruction

    # =================================== #
    # Views
    # =================================== #
    def sync_view(self, *_) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} must provide its own sync_view() implementation"
        )


