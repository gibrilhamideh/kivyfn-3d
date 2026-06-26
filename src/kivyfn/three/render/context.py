# kivyfn/three/render/context.py

# kivyfn/three/render/context.py

from __future__ import annotations

from pathlib import Path
from pprint import pformat
from typing import Any, Generic, Literal, TYPE_CHECKING, TypeVar

from kivy.event import EventDispatcher
from kivy.graphics import Callback, Instruction, InstructionGroup
from kivy.graphics import RenderContext as KivyRenderContext
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)

from kivyfn.three.graphics.gl import (
    GL,
    Fbo2D,
    FboCube,
    Texture2D,
    TextureCube,
    normalize_size,
)
from kivyfn.three.render.graphics.texture import BindTexture
from kivyfn.three.render.shader import Shader
from kivyfn.three.types import CubeFaceName
from kivyfn.three.views.view import BaseView, CubeView, View
from kivyfn.three.views.viewport import Viewport

if TYPE_CHECKING:
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.camera import Camera


ShaderReloadEvent = Literal[
    "manual",
    "modified",
    "created",
    "moved",
]


RenderOutput = Literal[
    "color",
    "depth",
    "normal",
    "position",
    "emissive",
    "material",
    "id",
]


TextureBindable = Texture2D | TextureCube


TContext = TypeVar(
    "TContext",
    KivyRenderContext,
    Fbo2D,
    FboCube,
)

TView = TypeVar(
    "TView",
    bound=BaseView,
)


class BaseContext(EventDispatcher, Generic[TContext, TView]):
    ctx: TContext

    texture_group: InstructionGroup
    render_group: InstructionGroup

    name: str = StringProperty()
    shader: Shader = ObjectProperty()
    hot_reload: bool = BooleanProperty(False)

    view: TView = ObjectProperty()
    output_texture: TextureBindable | None = ObjectProperty(
        None,
        allownone=True,
    )

    output_uniform: str = StringProperty()
    depth_test: bool = BooleanProperty(True)

    render_width: int = NumericProperty(0)
    render_height: int = NumericProperty(0)

    def _get_render_size(self) -> tuple[int, int]:
        return (
            int(self.render_width),
            int(self.render_height),
        )

    def _set_render_size(
        self,
        size: int | tuple[int, int],
    ) -> None:
        self.resize_render_area(
            normalize_size(size),
        )

    render_size = AliasProperty(
        _get_render_size,
        _set_render_size,
        bind=[
            "render_width",
            "render_height",
        ],
    )

    def _get_render_aspect(self) -> float:
        height = int(self.render_height)

        if height <= 0:
            return 1.0

        return int(self.render_width) / height

    render_aspect = AliasProperty(
        _get_render_aspect,
        None,
        bind=[
            "render_width",
            "render_height",
        ],
    )

    def __init__(
        self,
        *,
        view: TView,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.view = view
        self.output_texture = None

        self.texture_group = InstructionGroup()
        self.render_group = InstructionGroup()

        self._uniforms: dict[str, Any] = {}

    # =================================== #
    # Initialization
    # =================================== #
    def initialize(self) -> None:
        self.shader.bind(
            on_reload=self.on_shader_reload,
        )

        self.bind(
            hot_reload=self.shader.setter("hot_reload"),
        )

        self.view.bind(
            on_view_dirty=self.sync_view,
        )

        self.sync_render_area()
        self.sync_view()

    # =================================== #
    # Capabilities
    # =================================== #
    def require_view(self) -> TView:
        if self.view is None:
            raise TypeError(
                f"{type(self).__name__} {self.name!r} does not have a view."
            )

        return self.view

    def require_planar_view(self) -> View:
        view = self.require_view()

        if not isinstance(view, View):
            raise TypeError(
                f"{type(self).__name__} {self.name!r} does not have a planar View."
            )

        return view

    def require_cube_view(self) -> CubeView:
        view = self.require_view()

        if not isinstance(view, CubeView):
            raise TypeError(
                f"{type(self).__name__} {self.name!r} does not have a CubeView."
            )

        return view

    def require_viewport(self) -> Viewport:
        raise TypeError(
            f"{type(self).__name__} {self.name!r} does not have a viewport."
        )

    def require_output_texture(self) -> TextureBindable:
        if self.output_texture is None:
            raise TypeError(
                f"{type(self).__name__} {self.name!r} does not have an output texture."
            )

        return self.output_texture

    @property
    def has_viewport(self) -> bool:
        return False

    @property
    def has_output(self) -> bool:
        return self.output_texture is not None

    # =================================== #
    # Render Area
    # =================================== #
    def sync_render_area(
        self,
        *_: Any,
    ) -> None:
        pass

    def set_render_area(
        self,
        width: int,
        height: int,
    ) -> None:
        width = max(1, int(width))
        height = max(1, int(height))

        self.render_width = width
        self.render_height = height

    def get_render_size(self) -> tuple[int, int]:
        return (
            int(self.render_width),
            int(self.render_height),
        )

    def resize_render_area(
        self,
        size: int | tuple[int, int],
    ) -> None:
        raise TypeError(
            f"{type(self).__name__} {self.name!r} render area is not resizable."
        )

    # =================================== #
    # Texture Binding
    # =================================== #
    def bind_texture(
        self,
        *,
        uniform: str,
        texture: TextureBindable,
        slot: int,
    ) -> BindTexture:
        instruction = BindTexture(
            stage=self,
            uniform=uniform,
            texture=texture,
            slot=slot,
        )

        self.texture_group.add(instruction)

        self.apply_uniform(
            uniform,
            slot,
        )

        return instruction

    # =================================== #
    # Uniforms
    # =================================== #
    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self._uniforms[name] = value

        if isinstance(value, list):
            self.ctx[name] = value.copy()
        else:
            self.ctx[name] = value

        self.ask_update()

    def sync_uniforms(self) -> None:
        for key, value in list(self._uniforms.items()):
            self.apply_uniform(
                key,
                value,
            )

    @property
    def uniforms(self) -> dict[str, Any]:
        return self._uniforms

    # =================================== #
    # Shader
    # =================================== #
    def sync_shader(self) -> None:
        self.ctx.shader.vs = self.shader.vertex_source
        self.ctx.shader.fs = self.shader.fragment_source

        self.ctx.ask_update()
        self.sync_uniforms()
        self.sync_view()

    def on_shader_reload(
        self,
        shader: Shader,
        event_type: ShaderReloadEvent,
        path: Path | None,
    ) -> None:
        self.sync_shader()

    # =================================== #
    # View
    # =================================== #
    def sync_view(
        self,
        *_: Any,
    ) -> None:
        raise NotImplementedError(
            f"{type(self).__name__}.sync_view() must be implemented."
        )

    @property
    def projection_mat(self) -> Any:
        return self.ctx["projection_mat"]

    @property
    def view_mat(self) -> Any:
        return self.ctx["view_mat"]

    # =================================== #
    # Instructions
    # =================================== #
    def clear_textures(self) -> None:
        self.texture_group.clear()
        self.ask_update()

    def clear(self) -> None:
        self.texture_group.clear()
        self.render_group.clear()
        self.ask_update()

    def add(
        self,
        instruction: Instruction,
    ) -> None:
        self.render_group.add(instruction)
        self.ask_update()

    def remove(
        self,
        instruction: Instruction,
    ) -> None:
        self.render_group.remove(instruction)
        self.ask_update()

    def ask_update(self) -> None:
        self.ctx.ask_update()

    # =================================== #
    # GL State
    # =================================== #
    def enable_depthtest(
        self,
        *_: Any,
    ) -> None:
        GL.enable(GL.DEPTH_TEST)

    def disable_depthtest(
        self,
        *_: Any,
    ) -> None:
        GL.disable(GL.DEPTH_TEST)

    # =================================== #
    # Context Mirroring
    # =================================== #
    def __enter__(self):
        return self.ctx.__enter__()

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return self.ctx.__exit__(
            exc_type,
            exc,
            tb,
        )

    def __getitem__(
        self,
        name: str,
    ):
        return self.ctx[name]

    def __setitem__(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.apply_uniform(
            name,
            value,
        )

    # =================================== #
    # Destruction
    # =================================== #
    def destroy(self) -> None:
        self.shader.unbind(
            on_reload=self.on_shader_reload,
        )
        self.shader.destroy()

        delete = getattr(
            self.ctx,
            "delete",
            None,
        )

        if callable(delete):
            delete()


class RenderContext(BaseContext[KivyRenderContext, View]):
    viewport: Viewport = ObjectProperty()

    def __repr__(self) -> str:
        return (
            "RenderContext("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"render_size={self.render_size!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

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
        view: View | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            view=view or View(),
            **kwargs,
        )

        self.viewport = Viewport(
            scene=scene,
            local_x=local_x,
            local_y=local_y,
            local_width=local_width,
            local_height=local_height,
            viewport_mode=viewport_mode,
        )

        self.viewport.bind(
            on_viewport_dirty=self.on_viewport_dirty,
        )

        if camera is not None:
            camera.attach(
                self.require_planar_view(),
            )

        self.ctx = KivyRenderContext(
            vs=self.shader.vertex_source,
            fs=self.shader.fragment_source,
        )

        with self.ctx:
            Callback(self.viewport.apply)

            if self.depth_test:
                Callback(self.enable_depthtest)

            self.texture_group = InstructionGroup()
            self.render_group = InstructionGroup()

            if self.depth_test:
                Callback(self.disable_depthtest)

        self.initialize()

    @property
    def has_viewport(self) -> bool:
        return True

    def require_viewport(self) -> Viewport:
        return self.viewport

    def on_viewport_dirty(
        self,
        *_: Any,
    ) -> None:
        self.sync_render_area()
        self.sync_view()

    def sync_render_area(
        self,
        *_: Any,
    ) -> None:
        viewport = self.require_viewport()

        self.set_render_area(
            viewport.width,
            viewport.height,
        )

    def sync_view(
        self,
        *_: Any,
    ) -> None:
        viewport = self.require_viewport()
        view = self.require_planar_view()

        self.ctx["projection_mat"] = viewport.get_projection_matrix(
            view,
            uniform=True,
        )
        self.ctx["view_mat"] = viewport.get_view_matrix(
            view,
            uniform=True,
        )
        self.ctx["camera_position"] = view.get_camera_position()

        self.ctx.ask_update()


class RenderPass2D(BaseContext[Fbo2D, View]):
    size: list[int] = VariableListProperty(
        [1024, 1024],
        length=2,
    )

    push_viewport: bool = BooleanProperty(True)

    clear_color = ColorProperty(
        [0.0, 0.0, 0.0, 0.0],
    )
    clear_color_buffer: bool = BooleanProperty(True)
    clear_depth_buffer: bool = BooleanProperty(True)
    clear_stencil_buffer: bool = BooleanProperty(False)

    output: RenderOutput = OptionProperty(
        "depth",
        options=[
            "color",
            "depth",
            "normal",
            "position",
            "emissive",
            "material",
            "id",
        ],
    )

    def __repr__(self) -> str:
        return (
            "RenderPass2D("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"output={self.output!r}, "
            f"render_size={self.render_size!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        *,
        camera: Camera | None = None,
        texture: Texture2D | None = None,
        size: int | tuple[int, int] | None = None,
        view: View | None = None,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        **kwargs: Any,
    ) -> None:
        if size is not None:
            kwargs["size"] = list(
                normalize_size(size),
            )

        super().__init__(
            view=view or View(),
            **kwargs,
        )

        if camera is not None:
            camera.attach(
                self.require_planar_view(),
            )

        size = self.get_size()
        self.set_render_area(
            size[0],
            size[1],
        )

        self.output_texture = texture or Texture2D.empty(
            size,
            resizable=True,
        )

        self.ctx = Fbo2D(
            texture=self.output_texture,
            size=size,
            push_viewport=self.push_viewport,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
            clear_color=tuple(self.clear_color),
            clear_color_buffer=self.clear_color_buffer,
            clear_depth_buffer=self.clear_depth_buffer,
            clear_stencil_buffer=self.clear_stencil_buffer,
            depth_test=self.depth_test,
            vs=self.shader.vertex_source,
            fs=self.shader.fragment_source,
        )

        self.texture_group = self.ctx.texture_group
        self.render_group = self.ctx.render_group

        self.initialize()

    def initialize(self) -> None:
        super().initialize()

        self.bind(
            size=self.mark_size_dirty,
            push_viewport=self.sync_fbo_state,
            clear_color=self.sync_fbo_state,
            clear_color_buffer=self.sync_fbo_state,
            clear_depth_buffer=self.sync_fbo_state,
            clear_stencil_buffer=self.sync_fbo_state,
        )

        self.sync_fbo_state()

    def get_size(self) -> tuple[int, int]:
        width, height = normalize_size(
            (
                int(self.size[0]),
                int(self.size[1]),
            )
        )

        return (
            max(1, width),
            max(1, height),
        )

    def sync_render_area(
        self,
        *_: Any,
    ) -> None:
        width, height = self.get_size()

        self.set_render_area(
            width,
            height,
        )

    def resize_render_area(
        self,
        size: int | tuple[int, int],
    ) -> None:
        width, height = normalize_size(size)
        width = max(1, width)
        height = max(1, height)

        if self.get_size() == (width, height):
            return

        self.size = [
            width,
            height,
        ]

        self.sync_size()

    def mark_size_dirty(
        self,
        *_: Any,
    ) -> None:
        self.sync_size()

    def sync_size(self) -> None:
        size = self.get_size()

        if self.ctx.size != size:
            self.ctx.resize(size)
            self.output_texture = self.ctx.texture

        self.set_render_area(
            size[0],
            size[1],
        )

        self.sync_view()
        self.ask_update()

    def sync_fbo_state(
        self,
        *_: Any,
    ) -> None:
        self.ctx.push_viewport = self.push_viewport

        self.ctx.clear_color = tuple(self.clear_color)
        self.ctx.clear_color_buffer = self.clear_color_buffer
        self.ctx.clear_depth_buffer = self.clear_depth_buffer
        self.ctx.clear_stencil_buffer = self.clear_stencil_buffer

        self.ctx.ask_update()

    def sync_view(
        self,
        *_: Any,
    ) -> None:
        view = self.require_planar_view()

        self.ctx["projection_mat"] = view.get_projection_matrix(
            self.render_aspect,
        ).to_uniform()
        self.ctx["view_mat"] = view.get_view_matrix().to_uniform()
        self.ctx["camera_position"] = view.get_camera_position()

        self.ctx.ask_update()

    def get_pixel_color(
        self,
        x: int,
        y: int,
    ) -> Any:
        return self.ctx.get_pixel_color(
            x,
            y,
        )

    @property
    def pixels(self) -> Any:
        return self.ctx.read_pixels()

    @property
    def texture(self) -> Texture2D:
        texture = self.require_output_texture()

        if not isinstance(texture, Texture2D):
            raise TypeError(
                f"RenderPass2D {self.name!r} output texture is not Texture2D."
            )

        return texture


class RenderPassCube(BaseContext[FboCube, CubeView]):
    size: list[int] = VariableListProperty(
        [1024, 1024],
        length=2,
    )

    push_viewport: bool = BooleanProperty(True)

    clear_color = ColorProperty(
        [0.0, 0.0, 0.0, 0.0],
    )
    clear_color_buffer: bool = BooleanProperty(True)
    clear_depth_buffer: bool = BooleanProperty(True)
    clear_stencil_buffer: bool = BooleanProperty(False)

    output: RenderOutput = OptionProperty(
        "depth",
        options=[
            "color",
            "depth",
            "normal",
            "position",
            "emissive",
            "material",
            "id",
        ],
    )

    def __repr__(self) -> str:
        return (
            "RenderPassCube("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"output={self.output!r}, "
            f"render_size={self.render_size!r}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    def __init__(
        self,
        *,
        texture: TextureCube | None = None,
        size: int | tuple[int, int] | None = None,
        view: CubeView | None = None,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        **kwargs: Any,
    ) -> None:
        if size is not None:
            kwargs["size"] = list(
                normalize_size(size),
            )

        super().__init__(
            view=view or CubeView(),
            **kwargs,
        )

        size = self.get_size()
        self.set_render_area(
            size[0],
            size[1],
        )

        self.output_texture = texture or TextureCube.empty(
            size,
            resizable=True,
        )

        self.ctx = FboCube(
            texture=self.output_texture,
            size=size,
            push_viewport=self.push_viewport,
            face_callback=self.apply_cube_face,
            with_depthbuffer=with_depthbuffer,
            with_stencilbuffer=with_stencilbuffer,
            clear_color=tuple(self.clear_color),
            clear_color_buffer=self.clear_color_buffer,
            clear_depth_buffer=self.clear_depth_buffer,
            clear_stencil_buffer=self.clear_stencil_buffer,
            depth_test=self.depth_test,
            vs=self.shader.vertex_source,
            fs=self.shader.fragment_source,
        )

        self.texture_group = self.ctx.texture_group
        self.render_group = self.ctx.render_group

        self.initialize()

    def initialize(self) -> None:
        super().initialize()

        self.bind(
            size=self.mark_size_dirty,
            push_viewport=self.sync_fbo_state,
            clear_color=self.sync_fbo_state,
            clear_color_buffer=self.sync_fbo_state,
            clear_depth_buffer=self.sync_fbo_state,
            clear_stencil_buffer=self.sync_fbo_state,
        )

        self.sync_fbo_state()

    def get_size(self) -> tuple[int, int]:
        width, height = normalize_size(
            (
                int(self.size[0]),
                int(self.size[1]),
            )
        )

        width = max(1, width)
        height = max(1, height)

        if width != height:
            raise ValueError(
                f"RenderPassCube size must be square, got {width}x{height}."
            )

        return width, height

    def sync_render_area(
        self,
        *_: Any,
    ) -> None:
        width, height = self.get_size()

        self.set_render_area(
            width,
            height,
        )

    def resize_render_area(
        self,
        size: int | tuple[int, int],
    ) -> None:
        width, height = normalize_size(size)
        width = max(1, width)
        height = max(1, height)

        if width != height:
            raise ValueError(
                f"RenderPassCube linked size must be square, got {width}x{height}."
            )

        if self.get_size() == (width, height):
            return

        self.size = [
            width,
            height,
        ]

        self.sync_size()

    def mark_size_dirty(
        self,
        *_: Any,
    ) -> None:
        self.sync_size()

    def sync_size(self) -> None:
        size = self.get_size()

        if self.ctx.size != size:
            self.ctx.resize(size)
            self.output_texture = self.ctx.texture

        self.set_render_area(
            size[0],
            size[1],
        )

        self.sync_view()
        self.ask_update()

    def sync_fbo_state(
        self,
        *_: Any,
    ) -> None:
        self.ctx.push_viewport = self.push_viewport

        self.ctx.clear_color = tuple(self.clear_color)
        self.ctx.clear_color_buffer = self.clear_color_buffer
        self.ctx.clear_depth_buffer = self.clear_depth_buffer
        self.ctx.clear_stencil_buffer = self.clear_stencil_buffer

        self.ctx.ask_update()

    def sync_view(
        self,
        *_: Any,
    ) -> None:
        view = self.require_cube_view()

        self.ctx["projection_mat"] = view.get_projection_matrix().to_uniform()
        self.ctx["camera_position"] = view.get_camera_position()

        self.ctx.ask_update()

    def apply_cube_face(
        self,
        face_name: CubeFaceName,
    ) -> None:
        view = self.require_cube_view()

        self.ctx["view_mat"] = view.get_view_matrix(
            face_name,
        ).to_uniform()

    @property
    def texture(self) -> TextureCube:
        texture = self.require_output_texture()

        if not isinstance(texture, TextureCube):
            raise TypeError(
                f"RenderPassCube {self.name!r} output texture is not TextureCube."
            )

        return texture

    @property
    def faces(self):
        return self.ctx.faces


