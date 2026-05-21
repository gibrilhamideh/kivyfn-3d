# kivyfn/three/render/pass.py

from __future__ import annotations

from kivy.graphics import RenderContext

from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.cameranode import CameraNode


class RenderPass:
    def __init__(
        self,
        shader: Shader,
        *,
        compute_normal_mat: bool = True,
    ):
        self.shader = shader
        self.context = RenderContext(
            compute_normal_mat=compute_normal_mat,
        )

        self.context.shader.source = str(shader.path)

        for name, value in shader.uniforms.items():
            self.context[name] = value

    def __repr__(self) -> str:
        return f"RenderPass(shader={self.shader!r})"

    def clear(self) -> None:
        self.context.clear()

    def update_view(
        self,
        camera: CameraNode,
        aspect: float,
    ) -> None:
        self.context["projection_mat"] = (
            camera.get_projection_matrix(aspect)
        )

        self.context["modelview_mat"] = (
            camera.get_view_matrix()
        )

    @property
    def projection_mat(self):
        return self.context["projection_mat"]

    @property
    def modelview_mat(self):
        return self.context["modelview_mat"]
