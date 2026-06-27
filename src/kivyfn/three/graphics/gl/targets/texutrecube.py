# kivyfn/three/graphics/gl/fbo.py

from __future__ import annotations

from typing import Any
from collections.abc import Iterable
from functools import partial
from dataclasses import dataclass

from kivyfn.three.types import Color, CubeFaceName
from kivyfn.three.views.view import View
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.targets.base import BaseTargetContext, RenderFrame
from kivyfn.three.graphics.gl.texture import TextureCube
from kivyfn.three.graphics.gl.utils import normalize_size


CUBE_FACE_ORDER: tuple[CubeFaceName, ...] = (
    "px",
    "nx",
    "py",
    "ny",
    "pz",
    "nz",
)


CUBE_FACE_TARGETS: dict[CubeFaceName, int] = {
    "px": GL.CUBE_POSITIVE_X,
    "nx": GL.CUBE_NEGATIVE_X,
    "py": GL.CUBE_POSITIVE_Y,
    "ny": GL.CUBE_NEGATIVE_Y,
    "pz": GL.CUBE_POSITIVE_Z,
    "nz": GL.CUBE_NEGATIVE_Z,
}


@dataclass(slots=True)
class TextureCubeFace:
    name: CubeFaceName
    target: int
    framebuffer_id: int
    depthbuffer_id: int = 0
    stencilbuffer_id: int = 0



class TextureCubeTarget(BaseTargetContext):
    def __init__(
        self,
        *,
        view: View,
        viewport: Viewport,
        texture: TextureCube,
        attach_as: str,
        size: int | tuple[int, int] | None = None,
        clear_color: Color = (0.0, 0.0, 0.0, 0.0),
        clear_color_buffer: bool = True,
        clear_depth_buffer: bool = True,
        clear_stencil_buffer: bool = False,
        depth_test: bool = True,
        push_viewport: bool = True,
        with_depthbuffer: bool = True,
        with_stencilbuffer: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            view=view,
            viewport=viewport,
            **kwargs
        )

        width, height = texture.size if size is None else normalize_size(size)

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        if texture.size != (width, height):
            raise ValueError(
                f"TextureCube size {texture.size!r} does not match "
                f"TextureCubeTarget size {(width, height)!r}."
            )

        self._texture = texture
        self._attach_as = attach_as

        self._size = (width, height)
        self._width = width
        self._height = height


        self._with_depthbuffer = with_depthbuffer
        self._with_stencilbuffer = with_stencilbuffer

        self.clear_color = clear_color
        self.clear_color_buffer = clear_color_buffer
        self.clear_depth_buffer = clear_depth_buffer
        self.clear_stencil_buffer = clear_stencil_buffer

        self.depth_test = depth_test
        self.push_viewport = push_viewport

        self._faces: dict[CubeFaceName, TextureCubeFace] = {}

        self._previous_framebuffer = 0
        self._previous_renderbuffer = 0
        self._bound_face: CubeFaceName | None = None

        self.create_framebuffers()
        self.build(self.create_render_frames())



    # =================================== #
    # FrameBuffer
    # =================================== #

    def create_framebuffers(self) -> None:
        for face_name in CUBE_FACE_ORDER:
            self._faces[face_name] = self.create_face_framebuffers(
                face_name=face_name,
                target=CUBE_FACE_TARGETS[face_name],
            )

    def create_face_framebuffers(
        self,
        *,
        face_name: CubeFaceName,
        target: int,
    ) -> TextureCubeFace:
        previous_framebuffer = GL.get_int(GL.FRAMEBUFFER_BINDING)
        previous_renderbuffer = GL.get_int(GL.RENDERBUFFER_BINDING)

        framebuffer_id = GL.gen_framebuffer()
        depthbuffer_id = 0
        stencilbuffer_id = 0

        GL.bind_framebuffer(framebuffer_id)

        GL.attach_texture_2d(
            attachment=GL.COLOR_ATTACHMENT0,
            texture_target=target,
            id=self.texture.id,
        )

        if self.with_depthbuffer:
            depthbuffer_id = GL.gen_renderbuffer()

            GL.bind_renderbuffer(depthbuffer_id)
            GL.renderbuffer_storage(
                internal_format=GL.DEPTH_COMPONENT16,
                width=self.width,
                height=self.height,
            )
            GL.attach_renderbuffer(
                attachment=GL.DEPTH_ATTACHMENT,
                renderbuffer_id=depthbuffer_id,
            )

        if self.with_stencilbuffer:
            stencilbuffer_id = GL.gen_renderbuffer()

            GL.bind_renderbuffer(stencilbuffer_id)
            GL.renderbuffer_storage(
                internal_format=GL.STENCIL_INDEX8,
                width=self.width,
                height=self.height,
            )
            GL.attach_renderbuffer(
                attachment=GL.STENCIL_ATTACHMENT,
                renderbuffer_id=stencilbuffer_id,
            )

        status = GL.check_framebuffer_status()

        GL.bind_renderbuffer(previous_renderbuffer)
        GL.bind_framebuffer(previous_framebuffer)

        if status != GL.FRAMEBUFFER_COMPLETE:
            GL.delete_framebuffer(framebuffer_id)
            GL.delete_renderbuffer(depthbuffer_id)
            GL.delete_renderbuffer(stencilbuffer_id)

            raise RuntimeError(
                f"TextureCubeTarget framebuffer incomplete for face {face_name!r}. "
                f"Status: {status}"
            )

        return TextureCubeFace(
            name=face_name,
            target=target,
            framebuffer_id=framebuffer_id,
            depthbuffer_id=depthbuffer_id,
            stencilbuffer_id=stencilbuffer_id,
        )


    def create_render_frames(
        self,
    ) -> Iterable[RenderFrame]:
        return (
            RenderFrame(
                begin=partial(self.bind_face, face_name),
                apply=partial(self.sync_face_view, face_name),
                end=partial(self.release_face, face_name),
            )
            for face_name in CUBE_FACE_ORDER
        )

    # =================================== #
    # Bind / Release
    # =================================== #

    def bind_face(
        self,
        face_name: CubeFaceName,
        *_,
    ) -> None:
        if self._bound_face is not None:
            raise RuntimeError(
                f"TextureCubeTarget already has bound face {self._bound_face!r}."
            )

        face = self._faces[face_name]

        self._previous_framebuffer = GL.get_int(GL.FRAMEBUFFER_BINDING)
        self._previous_renderbuffer = GL.get_int(GL.RENDERBUFFER_BINDING)

        GL.bind_framebuffer(face.framebuffer_id)

        if self.push_viewport:
            self.viewport.override(
                x=0,
                y=0,
                width=self.width,
                height=self.height
            )

        else:
            self.viewport.apply()


        if self.depth_test:
            self.enable_depthtest()

        self._bound_face = face_name
        self.clear_framebuffer()

    def release_face(
        self,
        face: CubeFaceName,
        *_,
    ) -> None:
        if self._bound_face != face:
            raise RuntimeError(
                f"TextureCubeTarget cannot release face {face!r}; "
                f"currently bound face is {self._bound_face!r}."
            )

        if self.depth_test:
            self.disable_depthtest()

        self.viewport.restore()

        GL.bind_framebuffer(self._previous_framebuffer)
        GL.bind_renderbuffer(self._previous_renderbuffer)

        self._bound_face = None

    # =================================== #
    # Clear
    # =================================== #

    def clear_framebuffer(
        self,
    ) -> None:
        mask = 0

        if self.clear_color_buffer:
            r, g, b, a = self.clear_color

            GL.clear_color(
                r,
                g,
                b,
                a,
            )

            mask |= GL.COLOR_BUFFER_BIT

        if self.clear_depth_buffer and self.with_depthbuffer:
            mask |= GL.DEPTH_BUFFER_BIT

        if self.clear_stencil_buffer and self.with_stencilbuffer:
            mask |= GL.STENCIL_BUFFER_BIT

        if mask:
            GL.clear(mask)

    # =================================== #
    # Read
    # =================================== #
    def read_face_pixels(
        self,
        face_name: CubeFaceName,
        *,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        format: int = GL.RGBA,
        type: int = GL.UNSIGNED_BYTE,
    ) -> Any:
        if self._bound_face is not None and self._bound_face != face_name:
            raise RuntimeError(
                f"Cannot read face {face_name!r}; "
                f"currently bound face is {self._bound_face!r}."
            )

        face = self._faces[face_name]

        previous_framebuffer = GL.get_int(GL.FRAMEBUFFER_BINDING)
        previous_renderbuffer = GL.get_int(GL.RENDERBUFFER_BINDING)

        GL.bind_framebuffer(face.framebuffer_id)

        try:
            return GL.read_pixels(
                x=x,
                y=y,
                width=self.width if width is None else width,
                height=self.height if height is None else height,
                format=format,
                type=type,
            )
        finally:
            GL.bind_renderbuffer(previous_renderbuffer)
            GL.bind_framebuffer(previous_framebuffer)

    # =================================== #
    # Resize
    # =================================== #

    def resize(
        self,
        size: int | tuple[int, int],
    ) -> None:
        width, height = normalize_size(size)

        if width != height:
            raise ValueError(
                f"TextureCubeTarget size must be square, got {width}x{height}."
            )

        if self.size == (width, height):
            return

        self.texture.resize(
            (width, height),
        )

        self.delete_resources()

        self._size = (width, height)
        self._width = width
        self._height = height

        self.create_framebuffers()
        self.build(self.create_render_frames())


    # =================================== #
    # Delete
    # =================================== #

    def delete_resources(
        self,
    ) -> None:
        if self._bound_face is not None:
            self.release_face(self._bound_face)

        for face in self._faces.values():
            GL.delete_framebuffer(face.framebuffer_id)
            GL.delete_renderbuffer(face.depthbuffer_id)
            GL.delete_renderbuffer(face.stencilbuffer_id)

        self._faces.clear()

    def delete(
        self,
    ) -> None:
        self.delete_resources()
        self.clear_all()

    # =================================== #
    # Faces
    # =================================== #

    @property
    def faces(
        self,
    ) -> dict[CubeFaceName, TextureCubeFace]:
        return self._faces

    def sync_view(
        self,
        *_,
    ) -> None:

        view = self.view

        projection_mat = view.get_projection_matrix(mode="cube").to_uniform()
        self.apply_uniform("projection_mat", projection_mat)

        camera_position = view.get_camera_position()
        self.apply_uniform("camera_position", camera_position)

        self.ask_update()

    def sync_face_view(
        self,
        face: CubeFaceName,
        *_,
    ) -> None:

        view: View = self.view

        view_mat = view.get_view_matrix(mode="cube", face=face).to_uniform()
        self.apply_uniform("view_mat", view_mat)


    @property
    def texture(self) -> TextureCube:
        return self._texture

    @property
    def attach_as(self) -> str:
        return self._attach_as

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def with_depthbuffer(self) -> bool:
        return self._with_depthbuffer

    @property
    def with_stencilbuffer(self) -> bool:
        return self._with_stencilbuffer


