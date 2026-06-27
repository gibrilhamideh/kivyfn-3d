# kivyfn/three/graphics/gl/fbo.py

from __future__ import annotations

from typing import Any

from kivyfn.three.types import Color
from kivyfn.three.views.view import View
from kivyfn.three.views.viewport import Viewport
from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.targets.base import BaseTargetContext, RenderFrame
from kivyfn.three.graphics.gl.texture import Texture2D
from kivyfn.three.graphics.gl.utils import normalize_size

class Texture2DTarget(BaseTargetContext):
    def __init__(
        self,
        *,
        view: View,
        viewport: Viewport,
        texture: Texture2D,
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

        if texture.size != (width, height):
            raise ValueError(
                f"Texture2D size {texture.size!r} does not match "
                f"Fbo2D size {(width, height)!r}."
            )

        self.texture = texture
        self.attach_as = attach_as

        self.size = (width, height)
        self.width = width
        self.height = height

        self.clear_color = clear_color
        self.clear_color_buffer = clear_color_buffer
        self.clear_depth_buffer = clear_depth_buffer
        self.clear_stencil_buffer = clear_stencil_buffer

        self.push_viewport = push_viewport
        self.with_depthbuffer = with_depthbuffer
        self.with_stencilbuffer = with_stencilbuffer

        self.depth_test = depth_test
        self.framebuffer_id = 0
        self.depthbuffer_id = 0
        self.stencilbuffer_id = 0

        self._previous_framebuffer = 0
        self._previous_renderbuffer = 0
        self._bound = False

        self.create_framebuffer()

        self.build(
            RenderFrame(
                begin=self.bind,
                end=self.release,
            )
        )



    # =================================== #
    # Bind / Release
    # =================================== #
    def bind(
        self,
        *_: Any,
    ) -> None:
        if self._bound:
            raise RuntimeError("Fbo2D is already bound.")

        self._previous_framebuffer = GL.get_int(GL.FRAMEBUFFER_BINDING)
        self._previous_renderbuffer = GL.get_int(GL.RENDERBUFFER_BINDING)

        GL.bind_framebuffer(self.framebuffer_id)

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

        self._bound = True
        self.clear_framebuffer()

    def release(
        self,
        *_: Any,
    ) -> None:
        if not self._bound:
            raise RuntimeError("Fbo2D is not bound.")

        if self.depth_test:
            self.disable_depthtest()

        self.viewport.restore()

        GL.bind_framebuffer(self._previous_framebuffer)
        GL.bind_renderbuffer(self._previous_renderbuffer)

        self._bound = False

    # =================================== #
    # FrameBuffer
    # =================================== #
    def create_framebuffer(
        self,
    ) -> None:
        previous_framebuffer = GL.get_int(GL.FRAMEBUFFER_BINDING)
        previous_renderbuffer = GL.get_int(GL.RENDERBUFFER_BINDING)

        framebuffer_id = GL.gen_framebuffer()

        GL.bind_framebuffer(framebuffer_id)

        GL.attach_texture_2d(
            attachment=GL.COLOR_ATTACHMENT0,
            texture_target=self.texture.target,
            id=self.texture.id,
        )

        if self.with_depthbuffer:
            self.depthbuffer_id = GL.gen_renderbuffer()

            GL.bind_renderbuffer(self.depthbuffer_id)
            GL.renderbuffer_storage(
                internal_format=GL.DEPTH_COMPONENT16,
                width=self.width,
                height=self.height,
            )
            GL.attach_renderbuffer(
                attachment=GL.DEPTH_ATTACHMENT,
                renderbuffer_id=self.depthbuffer_id,
            )

        if self.with_stencilbuffer:
            self.stencilbuffer_id = GL.gen_renderbuffer()

            GL.bind_renderbuffer(self.stencilbuffer_id)
            GL.renderbuffer_storage(
                internal_format=GL.STENCIL_INDEX8,
                width=self.width,
                height=self.height,
            )
            GL.attach_renderbuffer(
                attachment=GL.STENCIL_ATTACHMENT,
                renderbuffer_id=self.stencilbuffer_id,
            )

        status = GL.check_framebuffer_status()

        GL.bind_renderbuffer(previous_renderbuffer)
        GL.bind_framebuffer(previous_framebuffer)

        if status != GL.FRAMEBUFFER_COMPLETE:
            GL.delete_framebuffer(framebuffer_id)
            GL.delete_renderbuffer(self.depthbuffer_id)
            GL.delete_renderbuffer(self.stencilbuffer_id)

            self.depthbuffer_id = 0
            self.stencilbuffer_id = 0

            raise RuntimeError(
                f"Texture2DTarget framebuffer incomplete. Status: {status}"
            )

        self.framebuffer_id = framebuffer_id

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

    def read_pixels(
        self,
        *,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        format: int = GL.RGBA,
        type: int = GL.UNSIGNED_BYTE,
    ) -> Any:
        should_release = False

        if not self._bound:
            self.bind()
            should_release = True

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
            if should_release:
                self.release()

    def get_pixel_color(
        self,
        x: int,
        y: int,
        *,
        format: int = GL.RGBA,
        type: int = GL.UNSIGNED_BYTE,
    ) -> Any:
        return self.read_pixels(
            x=x,
            y=y,
            width=1,
            height=1,
            format=format,
            type=type,
        )

    # =================================== #
    # Resize
    # =================================== #

    def resize(
        self,
        size: int | tuple[int, int],
    ) -> None:
        width, height = normalize_size(size)

        if self.size == (width, height):
            return

        self.texture.resize(
            (width, height),
        )

        self.delete_resources()

        self.size = (width, height)
        self.width = width
        self.height = height

        self.create_framebuffer()
        self.ask_update()

    # =================================== #
    # Delete
    # =================================== #

    def delete_resources(
        self,
    ) -> None:
        if self._bound:
            self.release()

        GL.delete_framebuffer(self.framebuffer_id)
        GL.delete_renderbuffer(self.depthbuffer_id)
        GL.delete_renderbuffer(self.stencilbuffer_id)

        self.framebuffer_id = 0
        self.depthbuffer_id = 0
        self.stencilbuffer_id = 0

    def delete(
        self,
    ) -> None:
        self.delete_resources()
        self.clear_all()

    # =================================== #
    # Views
    # =================================== #
    def sync_view(
        self,
        *_,
    ) -> None:

        view = self.view
        aspect = self.viewport.aspect

        projection_mat = view.get_projection_matrix(mode="planar", aspect=aspect).to_uniform()
        self.apply_uniform("projection_mat", projection_mat)

        view_mat = view.get_view_matrix(mode="planar").to_uniform()
        self.apply_uniform("view_mat", view_mat)

        camera_position = view.get_camera_position()
        self.apply_uniform("camera_position", camera_position)

        self.ask_update()





