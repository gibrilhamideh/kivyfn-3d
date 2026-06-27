# kivyfn/three/render/stage.py

from __future__ import annotations

from typing import Any, Literal, overload
from pathlib import Path
from pprint import pformat

from kivy.event import EventDispatcher
from kivy.graphics import Instruction
from kivy.properties import (
    BooleanProperty,
    ObjectProperty,
    StringProperty,
)

from kivyfn.three.views.view import View
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.render.config import RenderInstanceConfig
from kivyfn.three.render.shader import Shader
from kivyfn.three.graphics.gl import (
    BindTexture,
    Texture2D,
    TextureCube,
)

from kivyfn.three.graphics.gl.targets import (
    ScreenTarget,
    Texture2DTarget,
    TextureCubeTarget
)

from kivyfn.three.types import (
        StageTargets,
        RenderPassTarget,
        ShaderReloadEvent,
)



TextureBindable = Texture2D | TextureCube


TargetKind = Literal[
    "screen",
    "texture-2d",
    "texture-cube",
    "render-pass",
]


class RenderStage(EventDispatcher):

    name: str = StringProperty("")
    shader: Shader = ObjectProperty()
    target: StageTargets = ObjectProperty()
    hot_reload: bool = BooleanProperty(False)

    __events__ = (
        "on_view_dirty",
        "on_viewport_dirty"
    )

    def __init__(
        self,
        *,
        name: str,
        shader: Shader,
        target: StageTargets,
        hot_reload: bool = False,
        use_material: bool = True,
        use_textures: bool = True,
        use_render_id: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.name = name
        self.shader = shader
        self.target = target

        self.hot_reload = hot_reload

        self.instance_config = RenderInstanceConfig(
            use_material=use_material,
            use_textures=use_textures,
            use_render_id=use_render_id,
        )

        self._bind_events()
        self.sync_shader()

    # =================================== #
    # Representation
    # =================================== #

    def __repr__(self) -> str:
        return (
            "RenderStage("
            f"name={self.name!r}, "
            f"shader={self.shader.name!r}, "
            f"target={type(self.target).__name__}, "
            f"uniforms={pformat(self.uniforms)}"
            ")"
        )

    # =================================== #
    # Setup
    # =================================== #

    def _bind_events(self) -> None:
        self.shader.bind(
            on_reload=self.on_shader_reload,
        )

        self.bind(
            hot_reload=self.shader.setter("hot_reload"),
        )

        self.shader.hot_reload = self.hot_reload

        self.view.bind(on_dirty=self.mark_view_dirty)
        self.viewport.bind(on_dirty=self.mark_viewport_dirty)


    def _unbind_events(self) -> None:
        self.shader.unbind(
            on_reload=self.on_shader_reload,
        )

        self.unbind(
            hot_reload=self.shader.setter("hot_reload"),
        )

        self.view.unbind(on_dirty=self.mark_view_dirty)
        self.viewport.unbind(on_dirty=self.mark_viewport_dirty)


    # =================================== #
    # Target Type Helpers
    # =================================== #

    @property
    def is_screen(self) -> bool:
        return type(self.target) is ScreenTarget

    @property
    def is_texture_2d(self) -> bool:
        return type(self.target) is Texture2DTarget

    @property
    def is_texture_cube(self) -> bool:
        return type(self.target) is TextureCubeTarget


    # =================================== #
    # Uniforms
    # =================================== #
    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.target.apply_uniform(name, value)

    def sync_uniforms(self) -> None:
        self.target.sync_uniforms()

    @property
    def uniforms(self) -> dict[str, Any]:
        return self.target.uniforms

    # =================================== #
    # Shader
    # =================================== #
    def sync_shader(self) -> None:
        self.program.vs = self.shader.vertex_source
        self.program.fs = self.shader.fragment_source

        self.sync_uniforms()

    def on_shader_reload(
        self,
        shader: Shader,
        event_type: ShaderReloadEvent,
        path: Path | None,
    ) -> None:
        self.sync_shader()


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
        return self.target.bind_texture(
            uniform=uniform,
            texture=texture,
            slot=slot
        )

    def unbind_texture(
        self,
        instruction: BindTexture,
    ) -> None:
        self.target.remove_texture(instruction)
        self.ask_update()

    # =================================== #
    # Instructions
    # =================================== #

    def add(
        self,
        instruction: Instruction,
    ) -> None:
        self.target.add(instruction)

    def remove(
        self,
        instruction: Instruction,
    ) -> None:
        self.target.remove(instruction)

    def clear(self) -> None:
        self.target.clear()

    def ask_update(self) -> None:
        self.target.ask_update()

    def delete(self) -> None:
        self._unbind_events()
        self.target.delete()

    # =================================== #
    # Depth test
    # =================================== #
    @property
    def depth_test(self) -> bool:
        return self.target.depth_test

    @depth_test.setter
    def depth_test(self, value: bool) -> None:
        self.target.depth_test = value
        self.target.ask_update()

    # =================================== #
    # Dirty Flags
    # =================================== #
    def mark_view_dirty(self, view: View):
        self.dispatch("on_view_dirty", view)

    def mark_viewport_dirty(self, viewport: Viewport):
        self.dispatch("on_viewport_dirty", viewport)

    # =================================== #
    # Events
    # =================================== #
    def on_view_dirty(self, view: View):
        pass

    def on_viewport_dirty(self, viewport: Viewport):
        pass


    # =================================== #
    # Properties
    # =================================== #
    @property
    def program(self):
        """Kivy RenderContext shader program."""
        return self.target.shader

    @property
    def view(self) -> View:
        return self.target.view

    @property
    def viewport(self) -> Viewport:
        return self.target.viewport

    @property
    def use_material(
        self,
    ) -> bool:
        return self.instance_config.use_material

    @property
    def use_textures(
        self,
    ) -> bool:
        return self.instance_config.use_textures

    @property
    def use_render_id(
        self,
    ) -> bool:
        return self.instance_config.use_render_id

    # =================================== #
    # Reuiqre
    # =================================== #

    @overload
    def require_target(
        self,
        kind: Literal["screen"],
    ) -> ScreenTarget:
        ...


    @overload
    def require_target(
        self,
        kind: Literal["texture-2d"],
    ) -> Texture2DTarget:
        ...


    @overload
    def require_target(
        self,
        kind: Literal["texture-cube"],
    ) -> TextureCubeTarget:
        ...


    @overload
    def require_target(
        self,
        kind: Literal["render-pass"],
    ) -> RenderPassTarget:
        ...


    def require_target(
        self,
        kind: TargetKind,
    ) -> ScreenTarget | Texture2DTarget | TextureCubeTarget | RenderPassTarget:
        if kind == "screen":
            return self.target.as_screen

        if kind == "texture-2d":
            return self.target.as_texture_2d

        if kind == "texture-cube":
            return self.target.as_texture_cube

        if kind == "render-pass":
            if self.is_texture_2d:
                return self.target.as_texture_2d

            if self.is_texture_cube:
                return self.target.as_texture_cube

            raise TypeError(
                f"Render stage {self.name!r} is not a render-pass stage."
            )

        raise ValueError(
            f"Unknown target kind: {kind!r}."
        )



