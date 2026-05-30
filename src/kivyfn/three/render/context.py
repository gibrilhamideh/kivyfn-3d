# kivyfn/three/render/context.py

from __future__ import annotations

from pathlib import Path
from pprint import pformat
from typing import Any, Literal, TypeVar, Generic, TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics.texture import Texture
from kivy.graphics.opengl import (
    GL_DEPTH_TEST,
    glViewport,
    glDisable,
    glEnable,
)

from kivy.graphics import (
    BindTexture,
    Callback,
    InstructionGroup,
    ClearBuffers,
    Fbo as KivyFbo,
    RenderContext as KivyRenderContext,
)

from kivy.properties import (
    BooleanProperty,
    DictProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)

from kivyfn.three.render.shader import Shader

if TYPE_CHECKING:
    from kivyfn.three.scene.view import View

TContext = TypeVar(
    "TContext",
    KivyRenderContext,
    KivyFbo,
)


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


class BaseRenderContext(EventDispatcher, Generic[TContext]):

    ctx: TContext
    texture_group: InstructionGroup
    object_group: InstructionGroup

    x: float = NumericProperty(0.0)
    y: float = NumericProperty(0.0)
    width: float = NumericProperty(100.0)
    height: float = NumericProperty(100.0)

    scene_x: float = NumericProperty()
    scene_y: float = NumericProperty()
    scene_width: float = NumericProperty()
    scene_height: float = NumericProperty()

    use_local_viewport: bool = BooleanProperty(False)

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

    def __init__(
        self,
        shader: Shader,
        *,
        name: str = "",
        uniforms: dict | None = None,
        hot_reload: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.shader = shader
        self.name = name




        self.ctx.shader.source = str(shader.path)
        self.bind(hot_reload=shader.setter("hot_reload"))

        shader.bind(on_reload=self.on_shader_reload)
        self.hot_reload = hot_reload

        if uniforms is not None:
            self.uniforms = uniforms

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"framebuffer={self.framebuffer!r}, "
            f"output={self.output!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )


    # =================================== #
    # External API
    # =================================== #

    def set_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.uniforms[name] = value

    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.ctx[name] = value

    def sync_uniforms(self) -> None:
        for key, value in self.uniforms.items():
            self.apply_uniform(
                key,
                value,
            )

    def clear_textures(self) -> None:
        self.texture_group.clear()

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
        if path is None:
            return

        self.ctx.shader.source = str(path)
        self.sync_uniforms()
        self.ctx.ask_update()

    # =================================== #
    # Context Mirroring
    # =================================== #

    def __enter__(self):
        return self.ctx.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self.ctx.__exit__(
            exc_type,
            exc,
            tb,
        )

    def __getitem__(self, name: str):
        return self.ctx[name]

    def __setitem__(
        self,
        name: str,
        value: Any,
    ):
        self.set_uniform(
            name,
            value,
        )

    def clear(self) -> None:
        self.texture_group.clear()
        self.object_group.clear()

    def add(
        self,
        instruction,
    ) -> None:
        self.object_group.add(instruction)

    def remove(
        self,
        instruction,
    ) -> None:
        self.object_group.remove(instruction)

    # =================================== #
    # View & Projections
    # =================================== #

    def update_view(
        self,
        view: View,
        aspect: float,
    ) -> None:
        self.ctx["projection_mat"] = view.get_projection_matrix(aspect)
        self.ctx["view_mat"] = view.get_view_matrix()

    @property
    def projection_mat(self):
        return self.ctx["projection_mat"]

    @property
    def view_mat(self):
        return self.ctx["view_mat"]

    # =================================== #
    # Viewport
    # =================================== #

    def set_viewport(self, *_) -> None:
        x = self.x if self.use_local_viewport else self.scene_x
        y = self.y if self.use_local_viewport else self.scene_y
        width = self.width if self.use_local_viewport else self.scene_width
        height = self.height if self.use_local_viewport else self.scene_height

        glViewport(
            int(x),
            int(y),
            int(width),
            int(height),
        )

    @property
    def aspect(self) -> float:
        width = self.width if self.use_local_viewport else self.scene_width
        height = self.height if self.use_local_viewport else self.scene_height

        if not width:
            return 1.0

        if not height:
            return 1.0

        return width / height

    # =================================== #
    # Bindings
    # =================================== #
    def bind_texture(
        self,
        uniform: str,
        texture: Texture,
        slot: int,
    ) -> BindTexture:
        instruction = BindTexture(
            texture=texture,
            index=slot,
        )

        self.texture_group.add(instruction)

        self.set_uniform(
            uniform,
            slot,
        )

        return instruction


class RenderContext(BaseRenderContext[KivyRenderContext]):

    def __repr__(self) -> str:
        return (
            "RenderContext("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        shader: Shader,
        *,
        name: str = "",
        uniforms: dict | None = None,
        hot_reload: bool = False,
        **kwargs,
    ):


        self.ctx = KivyRenderContext()

        with self.ctx:
            Callback(self.set_viewport)
            Callback(self.enable_depthtest)

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        super().__init__(
            shader=shader,
            name=name,
            uniforms=uniforms,
            hot_reload=hot_reload,
            **kwargs,
        )

    # =================================== #
    # GL Context
    # =================================== #

    def enable_depthtest(self, *_):
        glEnable(GL_DEPTH_TEST)

    def disable_depthtest(self, *_):
        glDisable(GL_DEPTH_TEST)


class RenderPass(BaseRenderContext[KivyFbo]):

    def __repr__(self) -> str:
        return (
            "RenderPass("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"output={self.output!r}, "
            f"size={self.size!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        shader: Shader,
        *,
        name: str = "",
        size: tuple[int, int],
        uniforms: dict | None = None,
        hot_reload: bool = False,
        output: RenderPassOutput = "color",
        clear_color: tuple[float, float, float, float] = (
            1.0,
            1.0,
            1.0,
            1.0,
        ),
        with_depthbuffer: bool = True,
        **kwargs,
    ):
        self.size = size
        self.output = output
        self.clear_color = clear_color
        self.with_depthbuffer = with_depthbuffer

        self.use_local_viewport = True
        self.width, self.height = size

        self.ctx: KivyFbo = KivyFbo(
            size=self.size,
            clear_color=self.clear_color,
            with_depthbuffer=self.with_depthbuffer,
        )

        with self.ctx:
            Callback(self.set_viewport)

            ClearBuffers(
                clear_color=True,
                clear_depth=True,
            )

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

        super().__init__(
            shader=shader,
            name=name,
            uniforms=uniforms,
            hot_reload=hot_reload,
            output=output,
            **kwargs,
        )


    @property
    def texture(self) -> Texture:
        return self.ctx.texture
