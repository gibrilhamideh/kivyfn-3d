# kivyfn/three/render/context.py

from __future__ import annotations

from pathlib import Path
from pprint import pformat
from typing import Any, Literal, TypeVar, Generic, TYPE_CHECKING

from kivy.clock import Clock
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
    AliasProperty,
    BooleanProperty,
    ColorProperty,
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
    "id",
]


class BaseRenderContext(EventDispatcher, Generic[TContext]):

    ctx: TContext
    viewport_cb: Callback
    texture_group: InstructionGroup
    object_group: InstructionGroup


    name: str = StringProperty()
    shader: Shader = ObjectProperty()
    uniforms: dict = DictProperty()
    hot_reload: bool = BooleanProperty(False)

    use_local_viewport: bool = BooleanProperty(False)

    local_viewport_x: int = NumericProperty(0)
    local_viewport_y: int = NumericProperty(0)
    local_viewport_width: int = NumericProperty(100)
    local_viewport_height: int = NumericProperty(100)

    scene_x: float = NumericProperty(0)
    scene_y: float = NumericProperty(0)
    scene_width: float = NumericProperty(100)
    scene_height: float = NumericProperty(100)

    def _get_viewport_x(self):
        return self.local_viewport_x if self.use_local_viewport else int(self.scene_x)

    def _get_viewport_y(self):
        return self.local_viewport_y if self.use_local_viewport else int(self.scene_y)

    def _get_viewport_width(self):
        return self.local_viewport_width if self.use_local_viewport else int(self.scene_width)

    def _get_viewport_height(self):
        return self.local_viewport_height if self.use_local_viewport else int(self.scene_height)

    viewport_x = AliasProperty(
        _get_viewport_x,
        None,
        bind=["scene_x", "local_viewport_x", "use_local_viewport"]
    )

    viewport_y = AliasProperty(
        _get_viewport_y,
        None,
        bind=["scene_y", "local_viewport_y", "use_local_viewport"]
    )

    viewport_width = AliasProperty(
        _get_viewport_width,
        None,
        bind=["scene_width", "local_viewport_width", "use_local_viewport"]
    )

    viewport_height = AliasProperty(
        _get_viewport_height,
        None,
        bind=["scene_height", "local_viewport_height", "use_local_viewport"]
    )

    def _get_aspect(self) -> float:
        if not self.viewport_width:
            return 1.0

        if not self.viewport_height:
            return 1.0

        return self.viewport_width / self.viewport_height


    aspect: float = AliasProperty(
        _get_aspect,
        None,
        bind=["viewport_width", "viewport_height"]
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


    # =================================== #
    # Initialization
    # =================================== #
    def initialize(self):
        self.ctx.shader.source = str(self.shader.path)

        self.bind(hot_reload=self.shader.setter("hot_reload"))
        self.shader.bind(on_reload=self.on_shader_reload)



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
        self.ctx.ask_update()
        self.sync_uniforms()


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

    def update_view(self, view: View) -> None:
        self.ctx["projection_mat"] = view.get_projection_matrix(self.aspect)
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
    def _set_viewport(self, *_) -> None:

        # print(self.name, getattr(self, "fbo_size", None))
        glViewport(
            self.viewport_x,
            self.viewport_y,
            self.viewport_width,
            self.viewport_height,
        )

    # =================================== #
    # GL Context
    # =================================== #

    def enable_depthtest(self, *_):
        glEnable(GL_DEPTH_TEST)

    def disable_depthtest(self, *_):
        glDisable(GL_DEPTH_TEST)



class RenderContext(BaseRenderContext[KivyRenderContext]):

    def __repr__(self) -> str:
        return (
            "RenderContext("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ctx = KivyRenderContext()
        with self.ctx:
            self.viewport_cb = Callback(self._set_viewport)
            Callback(self.enable_depthtest)

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        self.initialize()




class RenderPass(BaseRenderContext[KivyFbo]):

    texture_ref: Texture = ObjectProperty(None, rebind=True)
    fbo_color = ColorProperty()
    fbo_width: int = NumericProperty(1024)
    fbo_height: int = NumericProperty(1024)
    use_viewport_size: bool = BooleanProperty(False)

    clear_color: bool = BooleanProperty(True)
    clear_depth: bool = BooleanProperty(True)
    clear_stencil: bool = BooleanProperty(False)

    def _get_fbo_size(self) -> tuple[int, int]:
        if self.use_viewport_size:
            return self.viewport_width, self.viewport_height

        return self.fbo_width, self.fbo_height

    fbo_size: tuple[int, int] = AliasProperty(
        _get_fbo_size,
        None,
        bind=[
            "fbo_width",
            "fbo_height",
            "viewport_width",
            "viewport_height",
            "use_viewport_size"
        ]

    )

    output: RenderPassOutput = OptionProperty(
        "depth",
        options=(
            "color",
            "depth",
            "normal",
            "position",
            "emissive",
            "material",
            "id",
        ),
    )

    def __repr__(self) -> str:
        return (
            "RenderPass("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"output={self.output!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        with_depthbuffer: bool,
        with_stencilbuffer: bool,
        **kwargs):

        super().__init__(**kwargs)

        self.ctx: KivyFbo = KivyFbo(
            size=(self.fbo_width, self.fbo_height),
            clear_color=self.fbo_color,
            push_viewport=False,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer
        )

        with self.ctx:

            self.viewport_cb = Callback(self._set_viewport)

            Callback(self.enable_depthtest)
            ClearBuffers(
                clear_color=self.clear_color,
                clear_depth=self.clear_depth,
                clear_stencil=self.clear_stencil
            )

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        self.initialize()


    def initialize(self):
        super().initialize()

        self.texture_ref = self.texture

        self.bind(fbo_size=self._update_fbo_size)
        self.bind(fbo_color=self._update_fbo_color)


    def _update_fbo_size(self, *_):
        old_texture = self.texture

        if self.ctx.size != self.fbo_size:
            self.ctx.size = self.fbo_size

        if self.ctx.texture is not old_texture:

            self.texture_ref = self.texture

    def _update_fbo_color(self, *_):
        self.ctx.clear_color = self.fbo_color


    def get_pixel_color(self, wx: int, wy: int):
        return self.ctx.get_pixel_color(wx, wy)


    @property
    def pixels(self):
        return self.ctx.pixels


    @property
    def texture(self) -> Texture:
        return self.ctx.texture
