# kivyfn/three/graphics/gl/bind.py

from __future__ import annotations

from typing import Any, Protocol

from kivy.graphics import Callback

from kivyfn.three.graphics.gl.core import GL


class UniformTarget(Protocol):
    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        ...


class TextureBindable(Protocol):
    target: int
    id: int


class BindTexture(Callback):
    def __init__(
        self,
        *,
        stage: UniformTarget,
        uniform: str,
        texture: TextureBindable,
        slot: int,
        **kwargs: Any,
    ) -> None:
        self.stage = stage
        self.uniform = uniform
        self.texture = texture
        self.slot = slot

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_: Any,
    ) -> None:
        GL.bind_texture_slot(
            target=self.texture.target,
            id=self.texture.id,
            slot=self.slot,
        )

        self.stage.apply_uniform(
            self.uniform,
            self.slot,
        )
