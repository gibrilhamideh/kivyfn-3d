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
    ColorProperty,
    DictProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    BooleanProperty,
    VariableListProperty,
)

from kivyfn.three.views.viewport import Viewport
from kivyfn.three.render.shader import Shader



if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.camera import Camera

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

    name: str = StringProperty()
    viewport: Viewport = ObjectProperty()
    shader: Shader = ObjectProperty()
    uniforms: dict = DictProperty()
    hot_reload: bool = BooleanProperty(False)


    def __init__(
        self,
        *,
        scene: Scene,
        camera: Camera | None,
        local_x: int,
        local_y: int,
        local_width: int,
        local_height: int,
        viewport_mode: Literal["scene", "local"],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.viewport = Viewport(
            scene=scene,
            local_x=local_x,
            local_y=local_y,
            local_width=local_width,
            local_height=local_height,
            viewport_mode=viewport_mode,
        )

        if camera is not None:
            camera.attach(self.viewport)


    # =================================== #
    # Initialization
    # =================================== #
    def initialize(self):

        self.shader.bind(on_reload=self.on_shader_reload)
        self.bind(hot_reload=self.shader.setter("hot_reload"))

        self.viewport.bind(on_view_dirty=self.sync_view)
        self.viewport.bind(on_viewport_dirty=self.sync_view)
        self.viewport.bind(on_viewport_dirty=self.viewport.apply)


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
        if isinstance(value, list):
            self.ctx[name] = value.copy()
        else:
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

    def sync_shader(self) -> None:
        self.ctx.shader.vs = self.shader.vertex_source
        self.ctx.shader.fs = self.shader.fragment_source

        self.ctx.ask_update()
        self.sync_uniforms()

    def on_shader_reload(
        self,
        shader: Shader,
        event_type: ShaderReloadEvent,
        path: Path | None,
    ) -> None:
        self.sync_shader()


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

    def ask_update(self) -> None:
        self.ctx.ask_update()


    # =================================== #
    # View & Projections
    # =================================== #
    def sync_view(self, *_) -> None:
        self.ctx["projection_mat"] = self.viewport.get_projection_matrix(
            uniform=True,
        )

        self.ctx["view_mat"] = self.viewport.get_view_matrix(
            uniform=True,
        )

        self.ctx["camera_position"] = self.viewport.get_camera_position()

    @property
    def projection_mat(self):
        return self.ctx["projection_mat"]

    @property
    def view_mat(self):
        return self.ctx["view_mat"]

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

        self.ctx = KivyRenderContext(
            vs=self.shader.vertex_source,
            fs=self.shader.fragment_source
        )
        with self.ctx:
            self.viewport_cb = Callback(self.viewport.apply)
            Callback(self.enable_depthtest)

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        self.initialize()




class RenderPass(BaseRenderContext[KivyFbo]):

    texture_ref: Texture = ObjectProperty()
    fbo_color = ColorProperty()
    fbo_size: list[int] = VariableListProperty([1024, 1024], length=2)
    fbo_size_mode: Literal["fixed", "viewport"] = OptionProperty(
        "fixed", options=["fixed", "viewport"]
    )

    clear_color: bool = BooleanProperty(True)
    clear_depth: bool = BooleanProperty(True)
    clear_stencil: bool = BooleanProperty(False)

    output = OptionProperty(
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
            size=self.fbo_size, # pyright: ignore
            push_viewport=False,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
            vs=self.shader.vertex_source,
            fs=self.shader.fragment_source
        )

        with self.ctx:

            self.viewport_cb = Callback(self.viewport.apply)

            Callback(self.enable_depthtest)
            ClearBuffers(
                clear_color=self.clear_color,
                clear_depth=self.clear_depth,
                clear_stencil=self.clear_stencil
            )

            self.clearcolor_inst = ClearColor(*self.fbo_color)

            self.texture_group = InstructionGroup()
            self.object_group = InstructionGroup()

            Callback(self.disable_depthtest)

        self.initialize()


    def initialize(self):
        super().initialize()

        self.texture_ref = self.texture

        self.viewport.bind(
            width=self.mark_size_dirty,
            height=self.mark_size_dirty
        )

        self.bind(fbo_size=self.mark_size_dirty)
        self.bind(fbo_color=self.sync_color)


    def mark_size_dirty(self, *_):
        self.sync_size()


    def sync_size(self):
        self.ctx.size = self.get_size() # pyright: ignore
        self.texture_ref = self.texture
        self.sync_view()

    def sync_color(self, *_):
        self.clearcolor_inst.rgba = self.fbo_color

    def get_size(self) -> list[int]:
        if self.fbo_size_mode == "fixed":
            return self.fbo_size

        else:
            return [
                self.viewport.width,
                self.viewport.height
            ]

    def get_pixel_color(self, wx: int, wy: int):
        return self.ctx.get_pixel_color(wx, wy)


    @property
    def pixels(self):
        return self.ctx.pixels


    @property
    def texture(self) -> Texture:
        return self.ctx.texture
