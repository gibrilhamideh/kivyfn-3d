# kivyfn/three/graphics/gl/core.py

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from array import array

from kivy.graphics.opengl import (

    # Texture constants
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_CUBE_MAP,
    GL_TEXTURE_CUBE_MAP_POSITIVE_X,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
    GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
    GL_TEXTURE_CUBE_MAP_NEGATIVE_Z,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_LINEAR_MIPMAP_NEAREST,
    GL_NEAREST_MIPMAP_LINEAR,
    GL_NEAREST_MIPMAP_NEAREST,



    # Formats
    GL_RGB,
    GL_RGBA,
    GL_UNSIGNED_BYTE,

    # Filters / wrapping
    GL_LINEAR,
    GL_NEAREST,
    GL_CLAMP_TO_EDGE,
    GL_REPEAT,
    GL_MIRRORED_REPEAT,

    # FBO / RBO constants
    GL_FRAMEBUFFER,
    GL_RENDERBUFFER,
    GL_FRAMEBUFFER_BINDING,
    GL_RENDERBUFFER_BINDING,
    GL_FRAMEBUFFER_COMPLETE,
    GL_COLOR_ATTACHMENT0,
    GL_DEPTH_ATTACHMENT,
    GL_STENCIL_ATTACHMENT,
    GL_DEPTH_COMPONENT16,
    GL_STENCIL_INDEX8,

    # State
    GL_VIEWPORT,
    GL_DEPTH_TEST,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_STENCIL_BUFFER_BIT,

    # Texture functions
    glActiveTexture,
    glBindTexture,
    glDeleteTextures,
    glGenTextures,
    glTexImage2D,
    glTexParameteri,
    glGenerateMipmap,

    # FBO / RBO functions
    glBindFramebuffer,
    glBindRenderbuffer,
    glCheckFramebufferStatus,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenRenderbuffers,
    glRenderbufferStorage,

    # State functions
    glGetError,
    glClear,
    glClearColor,
    glDisable,
    glEnable,
    glGetIntegerv,
    glViewport,

    # Readback
    glReadPixels,
)

try:
    from kivy.graphics.opengl import GL_TEXTURE_WRAP_R
except ImportError:
    GL_TEXTURE_WRAP_R = 0x8072


class GL:
    # =================================== #
    # Texture constants
    # =================================== #
    TEXTURE0 = GL_TEXTURE0

    TEXTURE_2D = GL_TEXTURE_2D
    TEXTURE_CUBE = GL_TEXTURE_CUBE_MAP

    CUBE_POSITIVE_X = GL_TEXTURE_CUBE_MAP_POSITIVE_X
    CUBE_NEGATIVE_X = GL_TEXTURE_CUBE_MAP_NEGATIVE_X
    CUBE_POSITIVE_Y = GL_TEXTURE_CUBE_MAP_POSITIVE_Y
    CUBE_NEGATIVE_Y = GL_TEXTURE_CUBE_MAP_NEGATIVE_Y
    CUBE_POSITIVE_Z = GL_TEXTURE_CUBE_MAP_POSITIVE_Z
    CUBE_NEGATIVE_Z = GL_TEXTURE_CUBE_MAP_NEGATIVE_Z

    TEXTURE_MIN_FILTER = GL_TEXTURE_MIN_FILTER
    TEXTURE_MAG_FILTER = GL_TEXTURE_MAG_FILTER
    TEXTURE_WRAP_S = GL_TEXTURE_WRAP_S
    TEXTURE_WRAP_T = GL_TEXTURE_WRAP_T
    TEXTURE_WRAP_R = GL_TEXTURE_WRAP_R

    REPEAT = GL_REPEAT
    MIRRORED_REPEAT = GL_MIRRORED_REPEAT
    CLAMP_TO_EDGE = GL_CLAMP_TO_EDGE


    NEAREST_MIPMAP_NEAREST = GL_NEAREST_MIPMAP_NEAREST
    LINEAR_MIPMAP_NEAREST = GL_LINEAR_MIPMAP_NEAREST
    NEAREST_MIPMAP_LINEAR = GL_NEAREST_MIPMAP_LINEAR
    LINEAR_MIPMAP_LINEAR = GL_LINEAR_MIPMAP_LINEAR

    # =================================== #
    # Formats
    # =================================== #
    RGB = GL_RGB
    RGBA = GL_RGBA
    UNSIGNED_BYTE = GL_UNSIGNED_BYTE

    # =================================== #
    # Filtering / wrapping
    # =================================== #
    LINEAR = GL_LINEAR
    NEAREST = GL_NEAREST

    CLAMP_TO_EDGE = GL_CLAMP_TO_EDGE
    REPEAT = GL_REPEAT
    MIRRORED_REPEAT = GL_MIRRORED_REPEAT

    # =================================== #
    # FBO / RBO constants
    # =================================== #
    FRAMEBUFFER = GL_FRAMEBUFFER
    RENDERBUFFER = GL_RENDERBUFFER

    FRAMEBUFFER_BINDING = GL_FRAMEBUFFER_BINDING
    RENDERBUFFER_BINDING = GL_RENDERBUFFER_BINDING
    FRAMEBUFFER_COMPLETE = GL_FRAMEBUFFER_COMPLETE

    COLOR_ATTACHMENT0 = GL_COLOR_ATTACHMENT0
    DEPTH_ATTACHMENT = GL_DEPTH_ATTACHMENT
    STENCIL_ATTACHMENT = GL_STENCIL_ATTACHMENT

    DEPTH_COMPONENT16 = GL_DEPTH_COMPONENT16
    STENCIL_INDEX8 = GL_STENCIL_INDEX8

    # =================================== #
    # State constants
    # =================================== #
    VIEWPORT = GL_VIEWPORT
    DEPTH_TEST = GL_DEPTH_TEST

    COLOR_BUFFER_BIT = GL_COLOR_BUFFER_BIT
    DEPTH_BUFFER_BIT = GL_DEPTH_BUFFER_BIT
    STENCIL_BUFFER_BIT = GL_STENCIL_BUFFER_BIT

    # =================================== #
    # Generic helpers
    # =================================== #
    @classmethod
    def gen_one(
        cls,
        func: Callable[[int], Any],
    ) -> int:
        value = func(1)

        if isinstance(value, (list, tuple)):
            value = value[0]

        return int(value)

    @classmethod
    def get_int(
        cls,
        name: int,
    ) -> int:
        value = glGetIntegerv(name)

        if isinstance(value, (list, tuple)):
            return int(value[0])

        return int(value)

    @classmethod
    def get_viewport(cls) -> tuple[int, int, int, int]:
        value = glGetIntegerv(GL_VIEWPORT)

        if isinstance(value, (list, tuple)):
            return (
                int(value[0]),
                int(value[1]),
                int(value[2]),
                int(value[3]),
            )

        return tuple(
            int(value[index])
            for index in range(4)
        )  # type: ignore[index]

    # =================================== #
    # Texture
    # =================================== #
    @staticmethod
    def tex_parameteri(
        target: int,
        pname: int,
        value: int,
    ) -> None:
        glTexParameteri(
            target,
            pname,
            value,
        )

    @staticmethod
    def generate_mipmap(
        target: int,
    ) -> None:
        glGenerateMipmap(target)

    @classmethod
    def gen_texture(cls) -> int:
        return cls.gen_one(glGenTextures)


    @classmethod
    def delete_texture(
        cls,
        id: int,
    ) -> None:
        if id:
            glDeleteTextures(
                1,
                cls.normalize_id(id),
            )

    @classmethod
    def bind_texture(
        cls,
        target: int,
        id: int,
    ) -> None:
        glBindTexture(target, id)

    @classmethod
    def unbind_texture(
        cls,
        target: int,
    ) -> None:
        glBindTexture(target, 0)

    @classmethod
    def active_texture(
        cls,
        slot: int,
    ) -> None:
        glActiveTexture(GL_TEXTURE0 + slot)

    @classmethod
    def bind_texture_slot(
        cls,
        *,
        target: int,
        id: int,
        slot: int,
    ) -> None:
        glActiveTexture(GL_TEXTURE0 + slot)
        glBindTexture(target, id)
        glActiveTexture(GL_TEXTURE0)

    @classmethod
    def create_texture(
        cls,
        target: int,
    ) -> int:
        id = cls.gen_texture()
        cls.bind_texture(
            target,
            id,
        )
        return id

    @classmethod
    def tex_image_2d(
        cls,
        *,
        target: int,
        width: int,
        height: int,
        pixels: bytes | memoryview | None = None,
        level: int = 0,
        internal_format: int | None = None,
        format: int | None = None,
        type: int | None = None,
        border: int = 0,
    ) -> None:
        color_format = GL_RGBA if format is None else format
        internal = color_format if internal_format is None else internal_format
        pixel_type = GL_UNSIGNED_BYTE if type is None else type

        glTexImage2D(
            target,
            level,
            internal,
            width,
            height,
            border,
            color_format,
            pixel_type,
            pixels,
        )


    @classmethod
    def configure_texture_2d(
        cls,
        *,
        min_filter: int | None = None,
        mag_filter: int | None = None,
        wrap_s: int | None = None,
        wrap_t: int | None = None,
    ) -> None:
        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MIN_FILTER,
            GL_LINEAR if min_filter is None else min_filter,
        )
        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MAG_FILTER,
            GL_LINEAR if mag_filter is None else mag_filter,
        )
        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_WRAP_S,
            GL_CLAMP_TO_EDGE if wrap_s is None else wrap_s,
        )
        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_WRAP_T,
            GL_CLAMP_TO_EDGE if wrap_t is None else wrap_t,
        )

    @classmethod
    def configure_texture_cube(
        cls,
        *,
        min_filter: int | None = None,
        mag_filter: int | None = None,
        wrap_s: int | None = None,
        wrap_t: int | None = None,
        wrap_r: int | None = None,
    ) -> None:
        glTexParameteri(
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_MIN_FILTER,
            GL_LINEAR if min_filter is None else min_filter,
        )
        glTexParameteri(
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_MAG_FILTER,
            GL_LINEAR if mag_filter is None else mag_filter,
        )
        glTexParameteri(
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_WRAP_S,
            GL_CLAMP_TO_EDGE if wrap_s is None else wrap_s,
        )
        glTexParameteri(
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_WRAP_T,
            GL_CLAMP_TO_EDGE if wrap_t is None else wrap_t,
        )
        glTexParameteri(
            GL_TEXTURE_CUBE_MAP,
            GL_TEXTURE_WRAP_R,
            GL_CLAMP_TO_EDGE if wrap_r is None else wrap_r,
        )

    # =================================== #
    # Framebuffer
    # =================================== #
    @classmethod
    def gen_framebuffer(cls) -> int:
        return cls.gen_one(glGenFramebuffers)

    @classmethod
    def delete_framebuffer(
        cls,
        framebuffer_id: int,
    ) -> None:
        if framebuffer_id:
            glDeleteFramebuffers(
                1,
                cls.normalize_id(framebuffer_id),
            )

    @classmethod
    def bind_framebuffer(
        cls,
        framebuffer_id: int,
    ) -> None:
        glBindFramebuffer(
            GL_FRAMEBUFFER,
            framebuffer_id,
        )

    @classmethod
    def unbind_framebuffer(cls) -> None:
        glBindFramebuffer(
            GL_FRAMEBUFFER,
            0,
        )

    @classmethod
    def attach_texture_2d(
        cls,
        *,
        attachment: int,
        texture_target: int,
        id: int,
        level: int = 0,
    ) -> None:
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            attachment,
            texture_target,
            id,
            level,
        )

    @classmethod
    def check_framebuffer_status(cls) -> int:
        return int(
            glCheckFramebufferStatus(GL_FRAMEBUFFER)
        )

    @classmethod
    def require_framebuffer_complete(
        cls,
        *,
        message: str = "Framebuffer incomplete.",
    ) -> None:
        status = cls.check_framebuffer_status()

        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(
                f"{message} Status: {status}"
            )

    # =================================== #
    # Renderbuffer
    # =================================== #
    @classmethod
    def gen_renderbuffer(cls) -> int:
        return cls.gen_one(glGenRenderbuffers)

    @classmethod
    def delete_renderbuffer(
        cls,
        renderbuffer_id: int,
    ) -> None:
        if renderbuffer_id:
            glDeleteRenderbuffers(
                1,
                cls.normalize_id(renderbuffer_id),
            )

    @classmethod
    def bind_renderbuffer(
        cls,
        renderbuffer_id: int,
    ) -> None:
        glBindRenderbuffer(
            GL_RENDERBUFFER,
            renderbuffer_id,
        )

    @classmethod
    def unbind_renderbuffer(cls) -> None:
        glBindRenderbuffer(
            GL_RENDERBUFFER,
            0,
        )

    @classmethod
    def renderbuffer_storage(
        cls,
        *,
        internal_format: int,
        width: int,
        height: int,
    ) -> None:
        glRenderbufferStorage(
            GL_RENDERBUFFER,
            internal_format,
            width,
            height,
        )

    @classmethod
    def attach_renderbuffer(
        cls,
        *,
        attachment: int,
        renderbuffer_id: int,
    ) -> None:
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER,
            attachment,
            GL_RENDERBUFFER,
            renderbuffer_id,
        )

    # =================================== #
    # State
    # =================================== #
    @classmethod
    def viewport(
        cls,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        glViewport(
            x,
            y,
            width,
            height,
        )

    @staticmethod
    def error() -> int:
        return int(glGetError())

    @classmethod
    def enable(
        cls,
        capability: int,
    ) -> None:
        glEnable(capability)

    @classmethod
    def disable(
        cls,
        capability: int,
    ) -> None:
        glDisable(capability)

    @classmethod
    def clear_color(
        cls,
        r: float,
        g: float,
        b: float,
        a: float,
    ) -> None:
        glClearColor(
            r,
            g,
            b,
            a,
        )

    @classmethod
    def clear(
        cls,
        mask: int,
    ) -> None:
        glClear(mask)

    @classmethod
    def read_pixels(
        cls,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        format: int | None = None,
        type: int | None = None,
    ) -> Any:
        return glReadPixels(
            x,
            y,
            width,
            height,
            GL_RGBA if format is None else format,
            GL_UNSIGNED_BYTE if type is None else type,
        )

    # =================================== #
    # depth test
    # =================================== #
    @staticmethod
    def normalize_id(
        id: int,
    ) -> bytes:
        return array("I", [int(id)]).tobytes()
