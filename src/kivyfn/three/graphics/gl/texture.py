# kivyfn/three/graphics/gl/texture.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from kivy.graphics.opengl import (
    GL_UNPACK_ALIGNMENT,
    glPixelStorei,
)

from kivyfn.three.graphics.gl.core import GL
from kivyfn.three.graphics.gl.utils import normalize_size
from kivyfn.three.images import Image, ImageLoader


Rgba = tuple[int, int, int, int]


TextureWrap = Literal[
    "repeat",
    "mirrored_repeat",
    "clamp_to_edge",
]

TextureMinFilter = Literal[
    "nearest",
    "linear",
    "nearest_mipmap_nearest",
    "linear_mipmap_nearest",
    "nearest_mipmap_linear",
    "linear_mipmap_linear",
]

TextureMagFilter = Literal[
    "nearest",
    "linear",
]


WRAP_MODES: dict[TextureWrap, int] = {
    "repeat": GL.REPEAT,
    "mirrored_repeat": GL.MIRRORED_REPEAT,
    "clamp_to_edge": GL.CLAMP_TO_EDGE,
}


FILTER_MODES: dict[TextureMinFilter | TextureMagFilter, int] = {
    "nearest": GL.NEAREST,
    "linear": GL.LINEAR,
    "nearest_mipmap_nearest": GL.NEAREST_MIPMAP_NEAREST,
    "linear_mipmap_nearest": GL.LINEAR_MIPMAP_NEAREST,
    "nearest_mipmap_linear": GL.NEAREST_MIPMAP_LINEAR,
    "linear_mipmap_linear": GL.LINEAR_MIPMAP_LINEAR,
}


MIPMAP_FILTERS: set[TextureMinFilter] = {
    "nearest_mipmap_nearest",
    "linear_mipmap_nearest",
    "nearest_mipmap_linear",
    "linear_mipmap_linear",
}


CUBE_FACE_TARGETS: tuple[int, ...] = (
    GL.CUBE_POSITIVE_X,
    GL.CUBE_NEGATIVE_X,
    GL.CUBE_POSITIVE_Y,
    GL.CUBE_NEGATIVE_Y,
    GL.CUBE_POSITIVE_Z,
    GL.CUBE_NEGATIVE_Z,
)


class TextureUtility:
    @staticmethod
    def is_power_of_two(
        value: int,
    ) -> bool:
        return value > 0 and (value & (value - 1)) == 0

    @staticmethod
    def is_pot_size(
        width: int,
        height: int,
    ) -> bool:
        return (
            TextureUtility.is_power_of_two(width)
            and TextureUtility.is_power_of_two(height)
        )

    @staticmethod
    def channels_for_format(
        format: int,
    ) -> int:
        if format == GL.RGBA:
            return 4

        if format == GL.RGB:
            return 3

        raise ValueError(
            f"Unsupported texture format: {format}"
        )

    @staticmethod
    def resolve_min_filter(
        *,
        mipmap: bool,
        min_filter: TextureMinFilter | None,
    ) -> TextureMinFilter:
        if min_filter is None:
            return (
                "linear_mipmap_linear"
                if mipmap
                else "linear"
            )

        if min_filter in MIPMAP_FILTERS and not mipmap:
            raise ValueError(
                f"min_filter={min_filter!r} requires mipmap=True."
            )

        return min_filter

    @staticmethod
    def validate_raw_options(
        *,
        width: int,
        height: int,
        mipmap: bool,
        wrap: TextureWrap,
    ) -> None:
        if TextureUtility.is_pot_size(
            width,
            height,
        ):
            return

        if mipmap:
            raise RuntimeError(
                f"Cannot generate mipmaps for NPOT texture {width}x{height}. "
                "Resize the image to power-of-two dimensions or use mipmap=False."
            )

        if wrap != "clamp_to_edge":
            raise RuntimeError(
                f"Cannot use wrap={wrap!r} for NPOT texture {width}x{height} "
                "in the raw OpenGL ES-style path. Use wrap='clamp_to_edge' "
                "or resize the image to power-of-two dimensions."
            )

    @staticmethod
    def require_non_mipmap_filter(
        *,
        owner: str,
        min_filter: TextureMinFilter,
    ) -> None:
        if min_filter not in MIPMAP_FILTERS:
            return

        raise ValueError(
            f"{owner} does not generate mipmaps. "
            f"Use a non-mipmap min_filter, got {min_filter!r}."
        )

    @staticmethod
    def upload_tex_image_2d(
        *,
        target: int,
        width: int,
        height: int,
        pixels: bytes | memoryview | None,
        format: int,
        type: int,
    ) -> None:
        # Standardized RGBA8 is tightly packed, so alignment=1 is always safe.
        # This also keeps the raw upload path safe for any future RGB uploads.
        glPixelStorei(
            GL_UNPACK_ALIGNMENT,
            1,
        )

        try:
            GL.tex_image_2d(
                target=target,
                width=width,
                height=height,
                pixels=pixels,
                format=format,
                type=type,
            )
        finally:
            glPixelStorei(
                GL_UNPACK_ALIGNMENT,
                4,
            )

    @staticmethod
    def configure_2d(
        *,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> None:
        wrap_value = WRAP_MODES[wrap]

        GL.tex_parameteri(
            GL.TEXTURE_2D,
            GL.TEXTURE_WRAP_S,
            wrap_value,
        )
        GL.tex_parameteri(
            GL.TEXTURE_2D,
            GL.TEXTURE_WRAP_T,
            wrap_value,
        )

        GL.tex_parameteri(
            GL.TEXTURE_2D,
            GL.TEXTURE_MIN_FILTER,
            FILTER_MODES[min_filter],
        )
        GL.tex_parameteri(
            GL.TEXTURE_2D,
            GL.TEXTURE_MAG_FILTER,
            FILTER_MODES[mag_filter],
        )

    @staticmethod
    def configure_cube(
        *,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> None:
        wrap_value = WRAP_MODES[wrap]

        GL.tex_parameteri(
            GL.TEXTURE_CUBE,
            GL.TEXTURE_WRAP_S,
            wrap_value,
        )
        GL.tex_parameteri(
            GL.TEXTURE_CUBE,
            GL.TEXTURE_WRAP_T,
            wrap_value,
        )
        GL.tex_parameteri(
            GL.TEXTURE_CUBE,
            GL.TEXTURE_WRAP_R,
            wrap_value,
        )

        GL.tex_parameteri(
            GL.TEXTURE_CUBE,
            GL.TEXTURE_MIN_FILTER,
            FILTER_MODES[min_filter],
        )
        GL.tex_parameteri(
            GL.TEXTURE_CUBE,
            GL.TEXTURE_MAG_FILTER,
            FILTER_MODES[mag_filter],
        )

    @staticmethod
    def create_empty_pixels(
        *,
        width: int,
        height: int,
        format: int,
        type: int,
    ) -> bytes:
        if type != GL.UNSIGNED_BYTE:
            raise ValueError(
                "Only GL.UNSIGNED_BYTE empty texture pixels are supported."
            )

        return bytes(
            width *
            height *
            TextureUtility.channels_for_format(format)
        )


class Texture2D:
    def __init__(
        self,
        *,
        id: int,
        size: tuple[int, int],
        resizable: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> None:
        self._id: int = id
        self._size: tuple[int, int] = size
        self._target: int = GL.TEXTURE_2D

        self._resizable: bool = resizable
        self._format: int = GL.RGBA
        self._type: int = GL.UNSIGNED_BYTE

        self._mipmap: bool = mipmap
        self._wrap: TextureWrap = wrap
        self._min_filter: TextureMinFilter = min_filter
        self._mag_filter: TextureMagFilter = mag_filter

    # =================================== #
    # Constructors
    # =================================== #

    @classmethod
    def from_source(
        cls,
        path: str | Path,
        *,
        flip_vertical: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        image = ImageLoader.from_source(
            path,
            flip_vertical=flip_vertical,
        )

        return cls.from_image(
            image,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        flip_vertical: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        image = ImageLoader.from_bytes(
            data,
            flip_vertical=flip_vertical,
        )

        return cls.from_image(
            image,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_image(
        cls,
        image: Image,
        *,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        if image.channels != 4:
            raise ValueError(
                f"Texture2D.from_image() expects 4 channels, got {image.channels}."
            )

        return cls.from_pixels(
            pixels=image.pixels,
            size=image.size,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_pixels(
        cls,
        *,
        pixels: bytes | memoryview,
        size: int | tuple[int, int],
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        width, height = normalize_size(size)

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=mipmap,
            wrap=wrap,
        )

        cls._validate_pixel_size(
            pixels=pixels,
            width=width,
            height=height,
        )

        resolved_min_filter = TextureUtility.resolve_min_filter(
            mipmap=mipmap,
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_2D,
        )

        try:
            TextureUtility.upload_tex_image_2d(
                target=GL.TEXTURE_2D,
                width=width,
                height=height,
                pixels=pixels,
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            TextureUtility.configure_2d(
                wrap=wrap,
                min_filter=resolved_min_filter,
                mag_filter=mag_filter,
            )

            if mipmap:
                GL.generate_mipmap(
                    GL.TEXTURE_2D,
                )

            GL.unbind_texture(
                GL.TEXTURE_2D,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_2D,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=False,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_rgba(
        cls,
        rgba: Rgba,
        *,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        TextureUtility.require_non_mipmap_filter(
            owner="Texture2D.from_rgba()",
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_2D,
        )

        try:
            TextureUtility.upload_tex_image_2d(
                target=GL.TEXTURE_2D,
                width=1,
                height=1,
                pixels=bytes(rgba),
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            TextureUtility.configure_2d(
                wrap=wrap,
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

            GL.unbind_texture(
                GL.TEXTURE_2D,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_2D,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=(1, 1),
            resizable=False,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def empty(
        cls,
        size: int | tuple[int, int],
        *,
        resizable: bool = True,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        width, height = normalize_size(
            size,
        )

        TextureUtility.require_non_mipmap_filter(
            owner="Texture2D.empty()",
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_2D,
        )

        try:
            TextureUtility.upload_tex_image_2d(
                target=GL.TEXTURE_2D,
                width=width,
                height=height,
                pixels=TextureUtility.create_empty_pixels(
                    width=width,
                    height=height,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                ),
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            TextureUtility.configure_2d(
                wrap=wrap,
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

            GL.unbind_texture(
                GL.TEXTURE_2D,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_2D,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=resizable,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    # =================================== #
    # Properties
    # =================================== #

    @property
    def id(
        self,
    ) -> int:
        return self._id

    @property
    def target(
        self,
    ) -> int:
        return self._target

    @property
    def size(
        self,
    ) -> tuple[int, int]:
        return self._size

    @property
    def width(
        self,
    ) -> int:
        return self._size[0]

    @property
    def height(
        self,
    ) -> int:
        return self._size[1]

    @property
    def resizable(
        self,
    ) -> bool:
        return self._resizable

    @property
    def format(
        self,
    ) -> int:
        return self._format

    @property
    def type(
        self,
    ) -> int:
        return self._type

    @property
    def mipmap(
        self,
    ) -> bool:
        return self._mipmap

    @property
    def wrap(
        self,
    ) -> TextureWrap:
        return self._wrap

    @property
    def min_filter(
        self,
    ) -> TextureMinFilter:
        return self._min_filter

    @property
    def mag_filter(
        self,
    ) -> TextureMagFilter:
        return self._mag_filter

    # =================================== #
    # Mutators
    # =================================== #

    def set_size(
        self,
        size: int | tuple[int, int],
    ) -> None:
        self.require_alive()

        if not self._resizable:
            raise RuntimeError(
                "Texture2D is not resizable."
            )

        width, height = normalize_size(
            size,
        )

        if self._size == (width, height):
            return

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=self._wrap,
        )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            TextureUtility.upload_tex_image_2d(
                target=self._target,
                width=width,
                height=height,
                pixels=TextureUtility.create_empty_pixels(
                    width=width,
                    height=height,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                ),
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            TextureUtility.configure_2d(
                wrap=self._wrap,
                min_filter=self._min_filter,
                mag_filter=self._mag_filter,
            )

            if self._mipmap:
                GL.generate_mipmap(
                    self._target,
                )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._size = (width, height)

    def set_pixels(
        self,
        pixels: bytes | memoryview,
        *,
        size: int | tuple[int, int] | None = None,
    ) -> None:
        self.require_alive()

        width, height = (
            self._size
            if size is None
            else normalize_size(size)
        )

        if size is not None and not self._resizable:
            if self._size != (width, height):
                raise RuntimeError(
                    "Texture2D is not resizable."
                )

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=self._wrap,
        )

        self._validate_pixel_size(
            pixels=pixels,
            width=width,
            height=height,
        )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            TextureUtility.upload_tex_image_2d(
                target=self._target,
                width=width,
                height=height,
                pixels=pixels,
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            TextureUtility.configure_2d(
                wrap=self._wrap,
                min_filter=self._min_filter,
                mag_filter=self._mag_filter,
            )

            if self._mipmap:
                GL.generate_mipmap(
                    self._target,
                )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._size = (width, height)

    def set_image(
        self,
        image: Image,
    ) -> None:
        if image.channels != 4:
            raise ValueError(
                f"Texture2D.set_image() expects 4 channels, got {image.channels}."
            )

        self.set_pixels(
            image.pixels,
            size=image.size,
        )

    def set_wrap(
        self,
        wrap: TextureWrap,
    ) -> None:
        self.require_alive()

        width, height = self._size

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=wrap,
        )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            wrap_value = WRAP_MODES[wrap]

            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_WRAP_S,
                wrap_value,
            )
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_WRAP_T,
                wrap_value,
            )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._wrap = wrap

    def set_filter(
        self,
        *,
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter | None = None,
    ) -> None:
        self.require_alive()

        resolved_min_filter = (
            self._min_filter
            if min_filter is None
            else min_filter
        )

        resolved_mag_filter = (
            self._mag_filter
            if mag_filter is None
            else mag_filter
        )

        if resolved_min_filter in MIPMAP_FILTERS and not self._mipmap:
            raise ValueError(
                f"min_filter={resolved_min_filter!r} requires mipmap=True."
            )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_MIN_FILTER,
                FILTER_MODES[resolved_min_filter],
            )
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_MAG_FILTER,
                FILTER_MODES[resolved_mag_filter],
            )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._min_filter = resolved_min_filter
        self._mag_filter = resolved_mag_filter

    def set_mipmap(
        self,
        enabled: bool,
    ) -> None:
        self.require_alive()

        if self._mipmap == enabled:
            return

        if enabled:
            width, height = self._size

            TextureUtility.validate_raw_options(
                width=width,
                height=height,
                mipmap=True,
                wrap=self._wrap,
            )

            GL.bind_texture(
                self._target,
                self._id,
            )

            try:
                GL.generate_mipmap(
                    self._target,
                )
            finally:
                GL.unbind_texture(
                    self._target,
                )

            self._mipmap = True

            if self._min_filter not in MIPMAP_FILTERS:
                self.set_filter(
                    min_filter="linear_mipmap_linear",
                )

            return

        if self._min_filter in MIPMAP_FILTERS:
            self.set_filter(
                min_filter="linear",
            )

        self._mipmap = False

    # =================================== #
    # Delete
    # =================================== #

    def delete(
        self,
    ) -> None:
        if self._id == 0:
            return

        GL.delete_texture(
            self._id,
        )
        self._id = 0

    def require_alive(
        self,
    ) -> None:
        if self._id == 0:
            raise RuntimeError(
                f"{type(self).__name__} has been deleted."
            )

    # =================================== #
    # Bind
    # =================================== #

    def bind(
        self,
    ) -> None:
        self.require_alive()

        GL.bind_texture(
            self._target,
            self._id,
        )

    def unbind(
        self,
    ) -> None:
        GL.unbind_texture(
            self._target,
        )

    def bind_to(
        self,
        slot: int,
    ) -> None:
        self.require_alive()

        GL.active_texture(
            int(slot),
        )

        self.bind()

    def unbind_from(
        self,
        slot: int,
    ) -> None:
        GL.active_texture(
            int(slot),
        )

        self.unbind()

    # =================================== #
    # Utility
    # =================================== #

    @staticmethod
    def _validate_pixel_size(
        *,
        pixels: bytes | memoryview,
        width: int,
        height: int,
    ) -> None:
        expected = width * height * 4
        actual = len(pixels)

        if actual != expected:
            raise ValueError(
                f"Pixel data size mismatch. Expected {expected} bytes "
                f"for RGBA texture size {(width, height)!r}, got {actual} bytes."
            )


class TextureCube:
    def __init__(
        self,
        *,
        id: int,
        size: tuple[int, int],
        resizable: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> None:
        self._id: int = id
        self._size: tuple[int, int] = size
        self._target: int = GL.TEXTURE_CUBE

        self._resizable: bool = resizable
        self._format: int = GL.RGBA
        self._type: int = GL.UNSIGNED_BYTE

        self._mipmap: bool = mipmap
        self._wrap: TextureWrap = wrap
        self._min_filter: TextureMinFilter = min_filter
        self._mag_filter: TextureMagFilter = mag_filter

    # =================================== #
    # Constructors
    # =================================== #

    @classmethod
    def from_source(
        cls,
        *,
        right: str | Path,
        left: str | Path,
        top: str | Path,
        bottom: str | Path,
        front: str | Path,
        back: str | Path,
        flip_vertical: bool = False,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        return cls.from_images(
            right=ImageLoader.from_source(
                right,
                flip_vertical=flip_vertical,
            ),
            left=ImageLoader.from_source(
                left,
                flip_vertical=flip_vertical,
            ),
            top=ImageLoader.from_source(
                top,
                flip_vertical=flip_vertical,
            ),
            bottom=ImageLoader.from_source(
                bottom,
                flip_vertical=flip_vertical,
            ),
            front=ImageLoader.from_source(
                front,
                flip_vertical=flip_vertical,
            ),
            back=ImageLoader.from_source(
                back,
                flip_vertical=flip_vertical,
            ),
            labels=(
                right,
                left,
                top,
                bottom,
                front,
                back,
            ),
            mipmap=mipmap,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_images(
        cls,
        *,
        right: Image,
        left: Image,
        top: Image,
        bottom: Image,
        front: Image,
        back: Image,
        labels: tuple[object, object, object, object, object, object] | None = None,
        mipmap: bool = False,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

        face_labels = labels or (
            "right",
            "left",
            "top",
            "bottom",
            "front",
            "back",
        )

        resolved_min_filter = TextureUtility.resolve_min_filter(
            mipmap=mipmap,
            min_filter=min_filter,
        )

        expected_size = cls._validate_images(
            faces=faces,
            labels=face_labels,
            mipmap=mipmap,
            wrap=wrap,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_CUBE,
        )

        try:
            for target, image in faces:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=image.width,
                    height=image.height,
                    pixels=image.pixels,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=wrap,
                min_filter=resolved_min_filter,
                mag_filter=mag_filter,
            )

            if mipmap:
                GL.generate_mipmap(
                    GL.TEXTURE_CUBE,
                )

            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=expected_size,
            resizable=False,
            mipmap=mipmap,
            wrap=wrap,
            min_filter=resolved_min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def from_rgba(
        cls,
        *,
        right: Rgba,
        left: Rgba,
        top: Rgba,
        bottom: Rgba,
        front: Rgba,
        back: Rgba,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        TextureUtility.require_non_mipmap_filter(
            owner="TextureCube.from_rgba()",
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_CUBE,
        )

        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

        try:
            for target, rgba in faces:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=1,
                    height=1,
                    pixels=bytes(rgba),
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=wrap,
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=(1, 1),
            resizable=False,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    @classmethod
    def empty(
        cls,
        size: int | tuple[int, int],
        *,
        resizable: bool = True,
        wrap: TextureWrap = "clamp_to_edge",
        min_filter: TextureMinFilter = "linear",
        mag_filter: TextureMagFilter = "linear",
    ) -> Self:
        width, height = normalize_size(
            size,
        )

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        TextureUtility.require_non_mipmap_filter(
            owner="TextureCube.empty()",
            min_filter=min_filter,
        )

        texture_id = GL.create_texture(
            GL.TEXTURE_CUBE,
        )

        pixels = TextureUtility.create_empty_pixels(
            width=width,
            height=height,
            format=GL.RGBA,
            type=GL.UNSIGNED_BYTE,
        )

        try:
            for target in CUBE_FACE_TARGETS:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=width,
                    height=height,
                    pixels=pixels,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=wrap,
                min_filter=min_filter,
                mag_filter=mag_filter,
            )

            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )

        except Exception:
            GL.unbind_texture(
                GL.TEXTURE_CUBE,
            )
            GL.delete_texture(
                texture_id,
            )
            raise

        return cls(
            id=texture_id,
            size=(width, height),
            resizable=resizable,
            mipmap=False,
            wrap=wrap,
            min_filter=min_filter,
            mag_filter=mag_filter,
        )

    # =================================== #
    # Properties
    # =================================== #

    @property
    def id(
        self,
    ) -> int:
        return self._id

    @property
    def target(
        self,
    ) -> int:
        return self._target

    @property
    def size(
        self,
    ) -> tuple[int, int]:
        return self._size

    @property
    def width(
        self,
    ) -> int:
        return self._size[0]

    @property
    def height(
        self,
    ) -> int:
        return self._size[1]

    @property
    def resizable(
        self,
    ) -> bool:
        return self._resizable

    @property
    def format(
        self,
    ) -> int:
        return self._format

    @property
    def type(
        self,
    ) -> int:
        return self._type

    @property
    def mipmap(
        self,
    ) -> bool:
        return self._mipmap

    @property
    def wrap(
        self,
    ) -> TextureWrap:
        return self._wrap

    @property
    def min_filter(
        self,
    ) -> TextureMinFilter:
        return self._min_filter

    @property
    def mag_filter(
        self,
    ) -> TextureMagFilter:
        return self._mag_filter

    # =================================== #
    # Mutators
    # =================================== #

    def set_size(
        self,
        size: int | tuple[int, int],
    ) -> None:
        self.require_alive()

        if not self._resizable:
            raise RuntimeError(
                "TextureCube is not resizable."
            )

        width, height = normalize_size(
            size,
        )

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        if self._size == (width, height):
            return

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=self._wrap,
        )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            pixels = TextureUtility.create_empty_pixels(
                width=width,
                height=height,
                format=GL.RGBA,
                type=GL.UNSIGNED_BYTE,
            )

            for target in CUBE_FACE_TARGETS:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=width,
                    height=height,
                    pixels=pixels,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=self._wrap,
                min_filter=self._min_filter,
                mag_filter=self._mag_filter,
            )

            if self._mipmap:
                GL.generate_mipmap(
                    self._target,
                )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._size = (width, height)

    def set_images(
        self,
        *,
        right: Image,
        left: Image,
        top: Image,
        bottom: Image,
        front: Image,
        back: Image,
        labels: tuple[object, object, object, object, object, object] | None = None,
    ) -> None:
        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

        face_labels = labels or (
            "right",
            "left",
            "top",
            "bottom",
            "front",
            "back",
        )

        size = self._validate_images(
            faces=faces,
            labels=face_labels,
            mipmap=self._mipmap,
            wrap=self._wrap,
        )

        if size != self._size and not self._resizable:
            raise RuntimeError(
                "TextureCube is not resizable."
            )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            for target, image in faces:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=image.width,
                    height=image.height,
                    pixels=image.pixels,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=self._wrap,
                min_filter=self._min_filter,
                mag_filter=self._mag_filter,
            )

            if self._mipmap:
                GL.generate_mipmap(
                    self._target,
                )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._size = size

    def set_pixels(
        self,
        *,
        right: bytes | memoryview,
        left: bytes | memoryview,
        top: bytes | memoryview,
        bottom: bytes | memoryview,
        front: bytes | memoryview,
        back: bytes | memoryview,
        size: int | tuple[int, int] | None = None,
    ) -> None:
        width, height = (
            self._size
            if size is None
            else normalize_size(size)
        )

        if width != height:
            raise ValueError(
                f"TextureCube size must be square, got {width}x{height}."
            )

        if (width, height) != self._size and not self._resizable:
            raise RuntimeError(
                "TextureCube is not resizable."
            )

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=self._wrap,
        )

        faces = (
            (GL.CUBE_POSITIVE_X, right),
            (GL.CUBE_NEGATIVE_X, left),
            (GL.CUBE_POSITIVE_Y, top),
            (GL.CUBE_NEGATIVE_Y, bottom),
            (GL.CUBE_POSITIVE_Z, front),
            (GL.CUBE_NEGATIVE_Z, back),
        )

        for _, pixels in faces:
            self._validate_pixel_size(
                pixels=pixels,
                width=width,
                height=height,
            )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            for target, pixels in faces:
                TextureUtility.upload_tex_image_2d(
                    target=target,
                    width=width,
                    height=height,
                    pixels=pixels,
                    format=GL.RGBA,
                    type=GL.UNSIGNED_BYTE,
                )

            TextureUtility.configure_cube(
                wrap=self._wrap,
                min_filter=self._min_filter,
                mag_filter=self._mag_filter,
            )

            if self._mipmap:
                GL.generate_mipmap(
                    self._target,
                )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._size = (width, height)

    def set_wrap(
        self,
        wrap: TextureWrap,
    ) -> None:
        self.require_alive()

        width, height = self._size

        TextureUtility.validate_raw_options(
            width=width,
            height=height,
            mipmap=self._mipmap,
            wrap=wrap,
        )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            wrap_value = WRAP_MODES[wrap]

            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_WRAP_S,
                wrap_value,
            )
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_WRAP_T,
                wrap_value,
            )
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_WRAP_R,
                wrap_value,
            )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._wrap = wrap

    def set_filter(
        self,
        *,
        min_filter: TextureMinFilter | None = None,
        mag_filter: TextureMagFilter | None = None,
    ) -> None:
        self.require_alive()

        resolved_min_filter: TextureMinFilter = (
            self._min_filter
            if min_filter is None
            else min_filter
        )

        resolved_mag_filter: TextureMagFilter = (
            self._mag_filter
            if mag_filter is None
            else mag_filter
        )

        if resolved_min_filter in MIPMAP_FILTERS and not self._mipmap:
            raise ValueError(
                f"min_filter={resolved_min_filter!r} requires mipmap=True."
            )

        GL.bind_texture(
            self._target,
            self._id,
        )

        try:
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_MIN_FILTER,
                FILTER_MODES[resolved_min_filter],
            )
            GL.tex_parameteri(
                self._target,
                GL.TEXTURE_MAG_FILTER,
                FILTER_MODES[resolved_mag_filter],
            )

        finally:
            GL.unbind_texture(
                self._target,
            )

        self._min_filter = resolved_min_filter
        self._mag_filter = resolved_mag_filter

    def set_mipmap(
        self,
        enabled: bool,
    ) -> None:
        self.require_alive()

        if self._mipmap == enabled:
            return

        if enabled:
            width, height = self._size

            TextureUtility.validate_raw_options(
                width=width,
                height=height,
                mipmap=True,
                wrap=self._wrap,
            )

            GL.bind_texture(
                self._target,
                self._id,
            )

            try:
                GL.generate_mipmap(
                    self._target,
                )
            finally:
                GL.unbind_texture(
                    self._target,
                )

            self._mipmap = True

            if self._min_filter not in MIPMAP_FILTERS:
                self.set_filter(
                    min_filter="linear_mipmap_linear",
                )

            return

        if self._min_filter in MIPMAP_FILTERS:
            self.set_filter(
                min_filter="linear",
            )

        self._mipmap = False

    # =================================== #
    # Delete
    # =================================== #

    def delete(
        self,
    ) -> None:
        if self._id == 0:
            return

        GL.delete_texture(
            self._id,
        )
        self._id = 0

    def require_alive(
        self,
    ) -> None:
        if self._id == 0:
            raise RuntimeError(
                f"{type(self).__name__} has been deleted."
            )

    # =================================== #
    # Bind
    # =================================== #

    def bind(
        self,
    ) -> None:
        self.require_alive()

        GL.bind_texture(
            self._target,
            self._id,
        )

    def unbind(
        self,
    ) -> None:
        GL.unbind_texture(
            self._target,
        )

    def bind_to(
        self,
        slot: int,
    ) -> None:
        self.require_alive()

        GL.active_texture(
            int(slot),
        )

        self.bind()

    def unbind_from(
        self,
        slot: int,
    ) -> None:
        GL.active_texture(
            int(slot),
        )

        self.unbind()

    # =================================== #
    # Utility
    # =================================== #

    @staticmethod
    def _validate_images(
        *,
        faces: tuple[
            tuple[int, Image],
            tuple[int, Image],
            tuple[int, Image],
            tuple[int, Image],
            tuple[int, Image],
            tuple[int, Image],
        ],
        labels: tuple[object, object, object, object, object, object],
        mipmap: bool,
        wrap: TextureWrap,
    ) -> tuple[int, int]:
        expected_size: tuple[int, int] | None = None

        for index, (_, image) in enumerate(faces):
            label = labels[index]

            if image.channels != 4:
                raise ValueError(
                    f"Cubemap face {label!r} expects 4 channels, "
                    f"got {image.channels}."
                )

            width = image.width
            height = image.height

            if width != height:
                raise ValueError(
                    f"Cubemap face must be square: "
                    f"{label!r} has size {width}x{height}."
                )

            TextureUtility.validate_raw_options(
                width=width,
                height=height,
                mipmap=mipmap,
                wrap=wrap,
            )

            if expected_size is None:
                expected_size = image.size
                continue

            if image.size != expected_size:
                raise ValueError(
                    "All cubemap faces must have the same size. "
                    f"Expected {expected_size}, "
                    f"got {image.size} for {label!r}."
                )

        if expected_size is None:
            raise RuntimeError(
                "Cubemap validation failed: no faces were provided."
            )

        return expected_size

    @staticmethod
    def _validate_pixel_size(
        *,
        pixels: bytes | memoryview,
        width: int,
        height: int,
    ) -> None:
        expected = width * height * 4
        actual = len(pixels)

        if actual != expected:
            raise ValueError(
                f"Pixel data size mismatch. Expected {expected} bytes "
                f"for RGBA cubemap face size {(width, height)!r}, got {actual} bytes."
            )
