# kivyfn/three/render/callbacks.py

from __future__ import annotations

from kivy.graphics import Callback

from kivyfn.three.render.stage import RenderStage
from kivyfn.three.math.matrix import Matrix3, Matrix4
from kivyfn.three.assets.material import Material


class TransformCallback(Callback):
    def __init__(
        self,
        *,
        stage: RenderStage,
        **kwargs,
    ):
        self.stage = stage

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
        self.stage.apply_uniform(
            "model_mat",
            self.model_mat.to_uniform(),
        )

        self.stage.apply_uniform(
            "normal_mat",
            self.normal_mat.to_uniform(),
        )

class GeometryCallback(Callback):
    def __init__(
        self,
        *,
        stage: RenderStage,
        has_tangents: bool,
        **kwargs,
    ) -> None:
        self.stage = stage
        self.has_tangents = has_tangents

        super().__init__(
            self.apply,
            **kwargs,
        )

    def apply(
        self,
        *_,
    ) -> None:
        self.stage.apply_uniform(
            "has_tangents",
            1 if self.has_tangents else 0,
        )

class MaterialCallback(Callback):
    def __init__(
        self,
        *,
        stage: RenderStage,
        material: Material,
        **kwargs,
    ) -> None:
        self.stage = stage
        self.material = material

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

            self.stage.apply_uniform(
                key,
                value,
            )


class ObjectIdCallback(Callback):
    def __init__(
        self,
        *,
        stage: RenderStage,
        render_id: int,
        uniform: str,
        **kwargs,
    ) -> None:
        self.stage = stage
        self.render_id = render_id
        self.uniform = uniform

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

        value = [
            r / 255.0,
            g / 255.0,
            b / 255.0,
            1.0,
        ]

        self.stage.apply_uniform(
            self.uniform,
            value,
        )


