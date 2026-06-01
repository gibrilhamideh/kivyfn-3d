# kivyfn/three/render/callbacks.py

from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import Callback

from kivyfn.three.math.matrix import Matrix3, Matrix4

if TYPE_CHECKING:
    from kivyfn.three.objects.material import Material
    from kivyfn.three.render.context import RenderContext, RenderPass


class TransformCallback(Callback):
    def __init__(
        self,
        *,
        ctx: RenderContext | RenderPass,
        **kwargs,
    ):
        self.ctx = ctx

        self.model_mat = Matrix4.identity()
        self.normal_mat = Matrix3.identity()

        super().__init__(
            self.apply,
            **kwargs,
        )

    def sync(
        self,
        model_mat: Matrix4,
        normal_mat: Matrix3,
    ) -> None:
        self.model_mat = model_mat
        self.normal_mat = normal_mat

        self.ask_update()

    def apply(self, *_):
        self.ctx.apply_uniform(
            "model_mat",
            self.model_mat.to_uniform(),
        )

        self.ctx.apply_uniform(
            "normal_mat",
            self.normal_mat.to_uniform(),
        )

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
        ctx: RenderContext | RenderPass,
        render_id: int,
        uniform_name: str,
        **kwargs,
    ) -> None:
        self.ctx = ctx
        self.render_id = render_id
        self.uniform_name = uniform_name

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_,
    ) -> None:
        render_id = self.render_id

        r = (render_id >> 16) & 0xFF
        g = (render_id >> 8) & 0xFF
        b = render_id & 0xFF

        # r = render_id & 0xFF
        # g = (render_id * 17) & 0xFF
        # b = (render_id * 53) & 0xFF

        id = [
            r / 255.0,
            g / 255.0,
            b / 255.0,
            1.0,
        ]

        self.ctx.apply_uniform(self.uniform_name, id)
