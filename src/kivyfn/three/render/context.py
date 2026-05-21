# kivyfn/three/render/context.py

from __future__ import annotations
from typing import Any

from kivy.properties import DictProperty, ObjectProperty, StringProperty
from kivy.graphics import RenderContext as KivyRenderContext
from kivy.event import EventDispatcher

from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.camera import Camera


class RenderContext(EventDispatcher):
    name: str = StringProperty()
    shader: Shader = ObjectProperty()
    uniforms: dict = DictProperty()

    def __repr__(self) -> str:
        return f"RenderPass(shader={self.shader!r})"

    def __init__(
        self,
        shader: Shader,
        *,
        name="",
        uniforms: dict | None = None,
        compute_normal_mat: bool = True,
    ):
        self.shader = shader
        self.name = name
        self.ctx = KivyRenderContext(compute_normal_mat=compute_normal_mat)
        self.ctx.shader.source = str(shader.path)

        if uniforms is not None:
            self.uniforms = uniforms

        for key, value in self.uniforms.items():
            self.ctx[key] = value

    def __enter__(self):
        return self.ctx.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self.ctx.__exit__(exc_type, exc, tb)

    def __getitem__(self, name: str):
        return self.ctx[name]

    def __setitem__(self, name: str, value: Any):
        self.ctx[name] = value

    def clear(self) -> None:
        self.ctx.clear()

    def update_view(
        self,
        camera: Camera,
        aspect: float,
    ) -> None:
        self.ctx["projection_mat"] = (
            camera.get_projection_matrix(aspect)
        )

        self.ctx["modelview_mat"] = (
            camera.get_view_matrix()
        )

    @property
    def projection_mat(self):
        return self.ctx["projection_mat"]

    @property
    def modelview_mat(self):
        return self.ctx["modelview_mat"]
