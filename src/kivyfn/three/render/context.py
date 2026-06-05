# kivyfn/three/render/context.py

from __future__ import annotations

from pathlib import Path
from pprint import pformat
from typing import Any, Literal, TypeVar, Generic, TYPE_CHECKING

from kivy.event import EventDispatcher
from kivy.graphics import ClearColor
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
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)

from kivyfn.three.render.shader import Shader
from kivyfn.three.render.link_filter import RenderLinkFilter

if TYPE_CHECKING:
    from kivyfn.three.views.view import View
    from kivyfn.three.types import RenderPassOutput

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



class BaseRenderContext(EventDispatcher, Generic[TContext]):

    ctx: TContext
    viewport_cb: Callback
    texture_group: InstructionGroup
    object_group: InstructionGroup
    link_filters: list[RenderLinkFilter] = ListProperty()


    name: str = StringProperty()
    shader: Shader = ObjectProperty()
    uniforms: dict = DictProperty()
    hot_reload: bool = BooleanProperty(False)

    use_local_viewport: bool = BooleanProperty(False)

    local_viewport_x: int = NumericProperty(0)
    local_viewport_y: int = NumericProperty(0)
    local_viewport_width: int = NumericProperty(100)
    local_viewport_height: int = NumericProperty(100)

    scene_viewport_x: int = NumericProperty(0)
    scene_viewport_y: int = NumericProperty(0)
    scene_viewport_width: int = NumericProperty(100)
    scene_viewport_height: int = NumericProperty(100)

    __events__ = (
        "on_viewport_dirty",
    )

    def _get_viewport_x(self):
        if self.use_local_viewport:
            return self.local_viewport_x + self.scene_viewport_x

        return self.scene_viewport_x

    def _get_viewport_y(self):
        if self.use_local_viewport:
            return self.local_viewport_y + self.scene_viewport_y

        return self.scene_viewport_y

    def _get_viewport_width(self):
        if self.use_local_viewport:
            return self.local_viewport_width

        return self.scene_viewport_width

    def _get_viewport_height(self):
        if self.use_local_viewport:
            return self.local_viewport_height

        return self.scene_viewport_height

    viewport_x = AliasProperty(
        _get_viewport_x,
        None,
        bind=["scene_viewport_x", "local_viewport_x", "use_local_viewport"]
    )

    viewport_y = AliasProperty(
        _get_viewport_y,
        None,
        bind=["scene_viewport_y", "local_viewport_y", "use_local_viewport"]
    )

    viewport_width = AliasProperty(
        _get_viewport_width,
        None,
        bind=["scene_viewport_width", "local_viewport_width", "use_local_viewport"]
    )

    viewport_height = AliasProperty(
        _get_viewport_height,
        None,
        bind=["scene_viewport_height", "local_viewport_height", "use_local_viewport"]
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

        self.bind(
            viewport_x=self.dispatch_viewport_dirty,
            viewport_y=self.dispatch_viewport_dirty,
            viewport_width=self.dispatch_viewport_dirty,
            viewport_height=self.dispatch_viewport_dirty,
        )


    # =================================== #
    # Bindings
    # =================================== #
    def create_texture_binder(
        self,
        output_uniform: str,
        texture: Texture,
        slot: int,
    ) -> BindTexture:

        instruction = BindTexture(
            texture=texture,
            index=slot,
        )

        self.texture_group.add(instruction)

        self.set_uniform(
            output_uniform,
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

    def dispatch_viewport_dirty(self, *_):
        self.dispatch("on_viewport_dirty")

    def on_viewport_dirty(self):
        pass

    # =================================== #
    # Viewport
    # =================================== #
    def _set_viewport(self, *_) -> None:
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

    texture_ref: Texture = ObjectProperty()
    fbo_color = ColorProperty()
    fbo_width: int = NumericProperty(1024)
    fbo_height: int = NumericProperty(1024)
    size_to_viewport: bool = BooleanProperty(False)

    clear_color: bool = BooleanProperty(True)
    clear_depth: bool = BooleanProperty(True)
    clear_stencil: bool = BooleanProperty(False)

    def _get_fbo_size(self) -> tuple[int, int]:
        if self.size_to_viewport:
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
            "size_to_viewport"
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

    output_uniform: str = StringProperty()

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
            size=self.fbo_size,
            push_viewport=False,
            # clear_color=self.fbo_color,
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

            self.clearcolor_instruction = ClearColor(*self.fbo_color)

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        self.initialize()


    def initialize(self):
        super().initialize()

        self.texture_ref = self.texture

        self.bind(fbo_size=self.sync_size)
        self.bind(fbo_color=self.sync_color)


    def sync_size(self, *_):
        self.ctx.size = self.fbo_size
        self.texture_ref = self.texture
        self.dispatch_viewport_dirty()

    def sync_color(self, *_):
        # self.ctx.clear_color = self.fbo_color
        self.clearcolor_instruction.rgba = self.fbo_color


    def get_pixel_color(self, wx: int, wy: int):
        return self.ctx.get_pixel_color(wx, wy)


    @property
    def pixels(self):
        return self.ctx.pixels


    @property
    def texture(self) -> Texture:
        return self.ctx.texture
