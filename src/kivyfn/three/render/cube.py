# kivyfn/three/render/cube.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

from kivy.graphics import Callback, InstructionGroup, RenderContext
from kivy.graphics.opengl import (
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT16,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_BINDING,
    GL_FRAMEBUFFER_COMPLETE,
    GL_RENDERBUFFER,
    GL_RENDERBUFFER_BINDING,
    GL_STENCIL_ATTACHMENT,
    GL_STENCIL_BUFFER_BIT,
    GL_STENCIL_INDEX8,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    GL_VIEWPORT,
    glBindFramebuffer,
    glBindRenderbuffer,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGetIntegerv,
    glRenderbufferStorage,
    glViewport,
)

if TYPE_CHECKING:
    from kivy.graphics.instructions import Instruction
    from kivyfn.three.render.resources import CubeTexture
    from kivyfn.three.render.shader import Shader
    from kivyfn.three.scene.scene import Scene
    from kivyfn.three.views.viewport import Viewport


CubeFaceName = Literal[
    "px",
    "nx",
    "py",
    "ny",
    "pz",
    "nz",
]


CUBE_FACE_ORDER: tuple[CubeFaceName, ...] = (
    "px",
    "nx",
    "py",
    "ny",
    "pz",
    "nz",
)


CUBE_FACE_TARGETS: dict[CubeFaceName, int] = {
    "px": GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    "nx": GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    "py": GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    "ny": GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    "pz": GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    "nz": GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
}


@dataclass(slots=True)
class CubeRenderFace:
    name: CubeFaceName
    target: int
    framebuffer_id: int
    depthbuffer_id: int
    stencilbuffer_id: int
    viewport: Viewport


class CubeRenderPass(RenderContext):
    def __init__(
        self,
        *,
        scene: Scene,
        name: str,
        shader: Shader,
        texture: CubeTexture,
        size: int,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        clear_color: bool = True,
        clear_depth: bool = True,
        clear_stencil: bool = False,
        clear_color_value: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        **kwargs: Any,
    ) -> None:
        super().__init__(
            use_parent_projection=False,
            use_parent_modelview=False,
            **kwargs,
        )

        if size <= 0:
            raise ValueError("CubeRenderPass size must be greater than zero.")

        if texture.size != (size, size):
            raise ValueError(
                f"CubeTexture size {texture.size!r} does not match CubeRenderPass size {(size, size)!r}."
            )

        self.scene = scene
        self.name = name
        self.stage_shader = shader
        self.texture = texture
        self.size = size

        self.with_depthbuffer = with_depthbuffer
        self.with_stencilbuffer = with_stencilbuffer

        self.clear_color = clear_color
        self.clear_depth = clear_depth
        self.clear_stencil = clear_stencil
        self.clear_color_value = clear_color_value

        self.object_group = InstructionGroup()
        self.faces: dict[CubeFaceName, CubeRenderFace] = {}
        self._uniforms: dict[str, Any] = {}

        self._previous_framebuffer = 0
        self._previous_renderbuffer = 0
        self._previous_viewport = (0, 0, 0, 0)
        self._bound_face: CubeFaceName | None = None
        self._destroyed = False

        for face_name in CUBE_FACE_ORDER:
            self.faces[face_name] = self._create_face(
                face_name=face_name,
                target=CUBE_FACE_TARGETS[face_name],
            )

        self._build()

    def _build(self) -> None:
        super().clear()

        for face_name in CUBE_FACE_ORDER:
            super().add(Callback(self._make_bind_callback(face_name)))
            super().add(self.object_group)
            super().add(Callback(self._make_release_callback(face_name)))

    def add(self, c: Instruction) -> None:
        self.require_alive()
        self.object_group.add(c)
        self.ask_update()

    def remove(self, c: Instruction) -> None:
        self.require_alive()
        self.object_group.remove(c)
        self.ask_update()

    def clear(self) -> None:
        self.require_alive()
        self.object_group.clear()
        self.ask_update()

    def apply_uniform(
        self,
        name: str,
        value: Any,
    ) -> None:
        self._uniforms[name] = value
        self[name] = value

    @property
    def uniforms(self) -> dict[str, Any]:
        return dict(self._uniforms)

    def _create_face(
        self,
        *,
        face_name: CubeFaceName,
        target: int,
    ) -> CubeRenderFace:
        from kivyfn.three.views.viewport import Viewport

        framebuffer_id = _gl_gen_one(glGenFramebuffers)
        depthbuffer_id = 0
        stencilbuffer_id = 0

        previous_framebuffer = _gl_get_int(GL_FRAMEBUFFER_BINDING)
        previous_renderbuffer = _gl_get_int(GL_RENDERBUFFER_BINDING)

        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer_id)

        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            target,
            self.texture.texture_id,
            0,
        )

        if self.with_depthbuffer:
            depthbuffer_id = _gl_gen_one(glGenRenderbuffers)
            glBindRenderbuffer(GL_RENDERBUFFER, depthbuffer_id)
            glRenderbufferStorage(
                GL_RENDERBUFFER,
                GL_DEPTH_COMPONENT16,
                self.size,
                self.size,
            )
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER,
                GL_DEPTH_ATTACHMENT,
                GL_RENDERBUFFER,
                depthbuffer_id,
            )

        if self.with_stencilbuffer:
            stencilbuffer_id = _gl_gen_one(glGenRenderbuffers)
            glBindRenderbuffer(GL_RENDERBUFFER, stencilbuffer_id)
            glRenderbufferStorage(
                GL_RENDERBUFFER,
                GL_STENCIL_INDEX8,
                self.size,
                self.size,
            )
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER,
                GL_STENCIL_ATTACHMENT,
                GL_RENDERBUFFER,
                stencilbuffer_id,
            )

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)

        glBindRenderbuffer(GL_RENDERBUFFER, previous_renderbuffer)
        glBindFramebuffer(GL_FRAMEBUFFER, previous_framebuffer)

        if status != GL_FRAMEBUFFER_COMPLETE:
            self._delete_framebuffer(framebuffer_id)
            self._delete_renderbuffer(depthbuffer_id)
            self._delete_renderbuffer(stencilbuffer_id)

            raise RuntimeError(
                f"Cube framebuffer incomplete for {self.name!r} face {face_name!r}: {status}"
            )

        viewport = Viewport(
            scene=self.scene,
            local_x=0,
            local_y=0,
            local_width=self.size,
            local_height=self.size,
            viewport_mode="local",
        )

        return CubeRenderFace(
            name=face_name,
            target=target,
            framebuffer_id=framebuffer_id,
            depthbuffer_id=depthbuffer_id,
            stencilbuffer_id=stencilbuffer_id,
            viewport=viewport,
        )

    def _make_bind_callback(
        self,
        face_name: CubeFaceName,
    ):
        def callback(*_: Any) -> None:
            self.bind_face(face_name)

        return callback

    def _make_release_callback(
        self,
        face_name: CubeFaceName,
    ):
        def callback(*_: Any) -> None:
            self.release_face(face_name)

        return callback

    def bind_face(
        self,
        face_name: CubeFaceName,
    ) -> None:
        self.require_alive()

        if self._bound_face is not None:
            raise RuntimeError(
                f"CubeRenderPass {self.name!r} already has bound face {self._bound_face!r}."
            )

        face = self.faces[face_name]

        self._previous_framebuffer = _gl_get_int(GL_FRAMEBUFFER_BINDING)
        self._previous_renderbuffer = _gl_get_int(GL_RENDERBUFFER_BINDING)
        self._previous_viewport = _gl_get_viewport()

        glBindFramebuffer(GL_FRAMEBUFFER, face.framebuffer_id)
        glViewport(0, 0, self.size, self.size)

        self._bound_face = face_name

        self.sync_face_view(face_name)
        self.clear_bound_face()

    def release_face(
        self,
        face_name: CubeFaceName,
    ) -> None:
        if self._bound_face != face_name:
            raise RuntimeError(
                f"CubeRenderPass {self.name!r} cannot release face {face_name!r}; "
                f"currently bound face is {self._bound_face!r}."
            )

        glBindFramebuffer(GL_FRAMEBUFFER, self._previous_framebuffer)
        glBindRenderbuffer(GL_RENDERBUFFER, self._previous_renderbuffer)

        x, y, width, height = self._previous_viewport
        glViewport(x, y, width, height)

        self._bound_face = None

    def sync_face_view(
        self,
        face_name: CubeFaceName,
    ) -> None:
        face = self.faces[face_name]

        self.apply_uniform(
            "projection_mat",
            face.viewport.get_projection_matrix(uniform=True),
        )

        self.apply_uniform(
            "view_mat",
            face.viewport.get_view_matrix(uniform=True),
        )

        self.apply_uniform(
            "camera_position",
            face.viewport.get_camera_position(),
        )

        self.apply_uniform(
            "cube_face",
            CUBE_FACE_ORDER.index(face_name),
        )

    def clear_bound_face(self) -> None:
        mask = 0

        if self.clear_color:
            r, g, b, a = self.clear_color_value
            glClearColor(r, g, b, a)
            mask |= GL_COLOR_BUFFER_BIT

        if self.clear_depth and self.with_depthbuffer:
            mask |= GL_DEPTH_BUFFER_BIT

        if self.clear_stencil and self.with_stencilbuffer:
            mask |= GL_STENCIL_BUFFER_BIT

        if mask:
            glClear(mask)

    def destroy(self) -> None:
        if self._destroyed:
            return

        if self._bound_face is not None:
            self.release_face(self._bound_face)

        self.object_group.clear()
        super().clear()

        for face in self.faces.values():
            self._delete_framebuffer(face.framebuffer_id)
            self._delete_renderbuffer(face.depthbuffer_id)
            self._delete_renderbuffer(face.stencilbuffer_id)

        self.faces.clear()
        self._destroyed = True

    def require_alive(self) -> None:
        if self._destroyed:
            raise RuntimeError(f"CubeRenderPass {self.name!r} has been destroyed.")

    @staticmethod
    def _delete_framebuffer(
        framebuffer_id: int,
    ) -> None:
        if framebuffer_id:
            glDeleteFramebuffers(1, framebuffer_id)

    @staticmethod
    def _delete_renderbuffer(
        renderbuffer_id: int,
    ) -> None:
        if renderbuffer_id:
            glDeleteRenderbuffers(1, renderbuffer_id)


def _gl_gen_one(func) -> int:
    value = func(1)

    if isinstance(value, (list, tuple)):
        value = value[0]

    return int(value)


def _gl_get_int(
    name: int,
) -> int:
    value = glGetIntegerv(name)

    if isinstance(value, (list, tuple)):
        return int(value[0])

    return int(value)


def _gl_get_viewport() -> tuple[int, int, int, int]:
    value = glGetIntegerv(GL_VIEWPORT)

    if isinstance(value, (list, tuple)):
        return (
            int(value[0]),
            int(value[1]),
            int(value[2]),
            int(value[3]),
        )

    return tuple(int(value[index]) for index in range(4))  # type: ignore[index]
