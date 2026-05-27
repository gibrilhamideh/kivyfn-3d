# kivyfn/three/render/context.py

from __future__ import annotations

from pathlib import Path
from pprint import pformat
from typing import Any, Literal, cast

from kivy.event import EventDispatcher
from kivy.graphics import (
    BindTexture,
    Fbo,
    RenderContext as KivyRenderContext,
)
from kivy.graphics.texture import Texture
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)

from kivyfn.three.render.shader import Shader
from kivyfn.three.scene.camera import Camera


ShaderReloadEvent = Literal[
    "manual",
    "modified",
    "created",
    "moved",
]

RenderPassOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "object_id",
]


class RenderContext(EventDispatcher):
    name: str = StringProperty()
    shader: Shader = ObjectProperty()
    uniforms: dict = DictProperty()
    hot_reload: bool = BooleanProperty(False)
    framebuffer: bool = BooleanProperty(False)

    output: RenderPassOutput = OptionProperty(
        "color",
        options=(
            "color",
            "depth",
            "normal",
            "position",
            "emissive",
            "material",
            "object_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            "RenderContext("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"framebuffer={self.framebuffer!r}, "
            f"output={self.output!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        shader: Shader,
        *,
        name: str = "",
        uniforms: dict | None = None,
        compute_normal_mat: bool = True,
        hot_reload: bool = False,
        framebuffer: bool = False,
        size: tuple[int, int] | None = None,
        output: RenderPassOutput = "color",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.shader = shader
        self.name = name
        self.framebuffer = framebuffer
        self.output = output

        if framebuffer:
            if size is None:
                raise ValueError(
                    "Framebuffer context requires a concrete size."
                )

            self.ctx = Fbo(
                size=size,
                with_depthbuffer=True,
                compute_normal_mat=compute_normal_mat,
            )

        else:
            self.ctx = KivyRenderContext(
                compute_normal_mat=compute_normal_mat,
            )

        self.ctx.shader.source = str(shader.path)

        self.bind(hot_reload=shader.setter("hot_reload"))
        shader.bind(on_reload=self.on_shader_reload)

        self.hot_reload = hot_reload

        if uniforms is not None:
            self.uniforms = uniforms

    # =================================== #
    # External API
    # =================================== #
    def set_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.uniforms[name] = value

    def sync_uniforms(self) -> None:
        for key, value in self.uniforms.items():
            self.ctx[key] = value

    def bind_texture(
        self,
        uniform: str,
        texture: Texture,
        slot: int,
    ) -> None:
        with self.ctx:
            BindTexture(
                texture=texture,
                index=slot,
            )

        self.ctx[uniform] = slot

    def unbind_texture(
        self,
        uniform: str,
    ) -> None:
        self.ctx[uniform] = 0

    def destroy(self) -> None:
        self.shader.unbind(on_reload=self.on_shader_reload)
        self.shader.destroy()
        self.ctx.clear()

    # =================================== #
    # Property Events
    # =================================== #
    def on_uniforms(self, *_):
        self.sync_uniforms()

    def on_shader_reload(
        self,
        shader: Shader,
        event_type: ShaderReloadEvent,
        path: Path | None,
    ) -> None:
        if path is not None:
            self.ctx.shader.source = str(path)
            self.sync_uniforms()
            self.ctx.ask_update()

    # =================================== #
    # Context Mirroring
    # =================================== #
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

    def add(self, instruction):
        self.ctx.add(instruction)

    def remove(self, instruction):
        self.ctx.remove(instruction)

    # =================================== #
    # View & Projections
    # =================================== #
    def update_view(
        self,
        camera: Camera,
        aspect: float,
    ) -> None:
        self.ctx["projection_mat"] = camera.get_projection_matrix(aspect)
        self.ctx["modelview_mat"] = camera.get_view_matrix()

    @property
    def projection_mat(self):
        return self.ctx["projection_mat"]

    @property
    def modelview_mat(self):
        return self.ctx["modelview_mat"]

    # =================================== #
    # Framebuffer
    # =================================== #
    @property
    def texture(self) -> Texture | None:
        if not self.framebuffer:
            return None

        ctx = cast(Fbo, self.ctx)
        return ctx.texture
