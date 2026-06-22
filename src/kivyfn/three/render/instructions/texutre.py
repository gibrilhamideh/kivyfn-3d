# kivyfn/three/render/instructions/texture.py

from __future__ import annotations

from typing import Any, Protocol

from kivy.graphics import Callback
from kivy.graphics.opengl import (
    GL_TEXTURE0,
    GL_TEXTURE_CUBE_MAP,
    glActiveTexture,
    glBindTexture,
)

from kivyfn.three.render.resources import CubeTexture


class UniformTarget(Protocol):
    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        ...


class BindCubeTexture(Callback):
    def __init__(
        self,
        *,
        stage: UniformTarget,
        uniform: str,
        texture: CubeTexture,
        slot: int,
        **kwargs,
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
        *_,
    ) -> None:
        glActiveTexture(GL_TEXTURE0 + self.slot)
        glBindTexture(
            GL_TEXTURE_CUBE_MAP,
            self.texture.texture_id,
        )

        self.stage.apply_uniform(
            self.uniform,
            self.slot,
        )
