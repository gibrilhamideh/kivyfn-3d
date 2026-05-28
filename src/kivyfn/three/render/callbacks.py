# kivyfn/three/render/callbacks.py

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from kivy.graphics import Callback, MatrixInstruction
from kivy.graphics.transformation import Matrix

from kivyfn.three.math.matrix import Matrix4

if TYPE_CHECKING:
    from kivyfn.three.objects.material import Material
    from kivyfn.three.render.context import RenderContext


class TransformCallback(Callback):
    def __init__(
        self,
        *,
        ctx: RenderContext,
        matrix_instruction: MatrixInstruction,
        **kwargs,
    ) -> None:
        self.ctx = ctx
        self.matrix_instruction = matrix_instruction

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_,
    ) -> None:
        self.ctx.apply_uniform("world_mat", self.matrix)

    # @property
    # def matrix(self):
    #     return self.matrix_instruction.matrix

    # @property
    # def matrix(self) -> Matrix:
    #     matrix4 = Matrix4(self.matrix_instruction.matrix.tolist())
    #     return matrix4.transpose().to_kivy_matrix()

    @property
    def matrix(self) -> Matrix:
        values = np.array(
            self.matrix_instruction.matrix.tolist(),
            dtype=np.float32,
        ).T

        matrix = Matrix()
        matrix.set(array=values.tolist())

        return matrix


class MaterialCallback(Callback):
    def __init__(
        self,
        *,
        ctx: RenderContext,
        material: Material,
        texture_slots: dict[str, int],
        **kwargs,
    ) -> None:
        self.ctx = ctx
        self.material = material
        self.texture_slots = texture_slots

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_,
    ) -> None:
        for key, value in self.material.uniforms.items():
            if value is None:
                continue

            if key in self.texture_slots:
                self.ctx.apply_uniform(
                    key,
                    self.texture_slots[key],
                )
                continue

            self.ctx.apply_uniform(
                key,
                value,
            )


class ObjectIdCallback(Callback):
    def __init__(
        self,
        *,
        ctx: RenderContext,
        object_id: int,
        uniform: str = "object_id_color",
        **kwargs,
    ) -> None:
        self.ctx = ctx
        self.object_id = object_id
        self.uniform = uniform

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_,
    ) -> None:
        object_id = self.object_id

        r = (object_id >> 16) & 0xFF
        g = (object_id >> 8) & 0xFF
        b = object_id & 0xFF

        self.ctx.apply_uniform(
            self.uniform,
            [
                r / 255.0,
                g / 255.0,
                b / 255.0,
                1.0,
            ],
        )
